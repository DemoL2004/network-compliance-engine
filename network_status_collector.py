from netmiko import ConnectHandler
from yaml import safe_load
import re
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from ipaddress import IPv4Network
from pathlib import Path
import logging

logger = logging.getLogger("collector")

def prefix_to_subnet(prefix):
    return str(
        IPv4Network(f"0.0.0.0/{prefix}").netmask
    )
def normalize_interface_name(interface):

    translations = {
        'vl': 'vlan',
        'po': 'port-channel',
        'gi': 'gigabitethernet',
        'fa': 'fastethernet',
        'te': 'tengigabitethernet',
        'lo': 'loopback'
    }

    interface = interface.strip()

    for short, full in translations.items():

        if interface.lower().startswith(full.lower()):
            return interface.lower()

        if interface.lower().startswith(short):
            return full + interface[len(short):]

    return interface

def collect_device(device_details,config):
    device_info,details=device_details
    device = {
        "device_type": "cisco_ios",
        "host": details.get("ip"),
        "username": config.get("username"),
        "password": config.get("password"),
        "secret": config.get("secret")
    }


    try:
        logger.info(f"STARTING COLLECTION FOR {device_info}")
        conn = ConnectHandler(**device)
        conn.enable()
        health_data = {
            "ip_routing": True,
            "vlans":{},
            "interfaces": {},
            "stp": {},
            "ospf": {},
            "hsrp": {},
            "etherchannel": {},
            'dhcp':{}
        }
        output = conn.send_command(
            "show running-config | include ip routing"
        )
        if output:
            health_data['ip_routing']=False
        vlan_name=conn.send_command("show vlan brief ", use_textfsm=True)
        current_vlans=[]
        for vlan in vlan_name:
            if vlan.get('status')=='active' and vlan.get('vlan_id')!='1':
                health_data['vlans'][vlan.get('vlan_id')]={'name':vlan.get('vlan_name')}
                current_vlans.append(int(vlan["vlan_id"]))


        interface_list = conn.send_command("show ip int ", use_textfsm=True)

        for interface in interface_list:
            ip = interface.get('ip_address')
            if ip:
                health_data['interfaces'][normalize_interface_name(interface.get('interface'))] = {
                    "ip": ip[0],
                    "status": interface.get("link_status"),
                    'subnet': prefix_to_subnet(interface.get('prefix_length')[0])
                }
                if 'Vlan' in interface.get('interface'):
                    health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['type']='svi'
                else:
                    health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['type']='routed'
                acls = {}

                if interface.get('inbound_acl'):
                    acls['in'] = {
                        'name': interface['inbound_acl']
                    }
                if interface.get('outgoing_acl'):
                    acls['out'] = {
                        'name': interface['outgoing_acl']
                    }
                if acls:
                    health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['acl'] = acls
                    for direction in acls:
                        acl= conn.send_command(f"show access-list {acls[direction]['name']} ", use_textfsm=True)

                        health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['acl'][
                            direction]['seq'] = {}
                        for seq in acl:
                            health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['acl'][
                                direction]['mode'] = seq.get('type').lower()
                            source_parts = seq.get('source').split()

                            health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['acl'][direction]['seq'][seq.get('sn')]={
                                'action': seq.get('action'),
                                'source_network': source_parts[0]
                            }
                            if len(source_parts) > 1:
                                health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['acl'][direction]['seq'][seq.get('sn')]['source_wildcard']=source_parts[1]
                            destination_parts = seq.get('destination').split()
                            health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['acl'][direction]['seq'][seq.get('sn')]['destination_network'] = destination_parts[0]
                            if len(destination_parts) > 1:
                                health_data['interfaces'][normalize_interface_name(interface.get('interface'))]['acl'][direction]['seq'][seq.get('sn')]['destination_wildcard'] = destination_parts[1]

        switchport_list=conn.send_command("show int switchport ", use_textfsm=True)
        for switchport in switchport_list:
            if switchport.get('mode') != 'down':
                interface = normalize_interface_name(switchport.get('interface'))
                mode = switchport.get('admin_mode')

                if mode == "static access":

                    health_data['interfaces'][interface] = {
                        'type':'switchport',
                        'mode': 'access',
                        'vlan': int(switchport.get('access_vlan'))
                    }

                elif mode == "trunk":

                    health_data['interfaces'][interface] = {
                        'type': 'switchport',
                        'mode': 'trunk',
                        'vlans': [
                            int(vlan)
                            for vlan in switchport.get('trunking_vlans')
                        ]
                    }

                elif mode == "dynamic auto":

                    health_data['interfaces'][interface] = {
                        'type': 'switchport',
                        'mode': 'dynamic auto'
                    }

                else:

                    health_data['interfaces'][interface] = {
                        'type': 'switchport',
                        'mode': mode
                    }


        dhcp_pool_list = conn.send_command("show run | include dhcp pool")
        if dhcp_pool_list:
            for dhcp in dhcp_pool_list.splitlines():

                dhcp_name = dhcp.split()[-1]

                dhcp_config = conn.send_command(
                    f"show run | section dhcp pool {dhcp_name}"
                )

                network_match = re.search(
                    r'network (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)',
                    dhcp_config
                )

                default_match = re.search(
                    r'default-router (\d+\.\d+\.\d+\.\d+)',
                    dhcp_config
                )

                health_data['dhcp'][dhcp_name] = {}

                if network_match:
                    health_data['dhcp'][dhcp_name]['ip'] = network_match.group(1)
                    health_data['dhcp'][dhcp_name]['subnet'] = network_match.group(2)

                if default_match:
                    health_data['dhcp'][dhcp_name]['default_gateway'] = default_match.group(1)

                dns_match = re.search(
                    r'dns-server (\d+\.\d+\.\d+\.\d+)',
                    dhcp_config
                )

                if dns_match:
                    health_data['dhcp'][dhcp_name]['dns'] = dns_match.group(1)

                lease_match = re.search(
                    r'lease (.+)',
                    dhcp_config
                )

                if lease_match:
                    health_data['dhcp'][dhcp_name]['lease'] = lease_match.group(1)



        for vlan_id in current_vlans:
            vlan_prio = conn.send_command(f"sh span bridge prio | include {vlan_id:04d}", use_textfsm=True)
            if not vlan_prio.strip():
                continue

            priority = int(vlan_prio.split(" ")[-1])
            health_data['stp'][vlan_id] = {'role': False, 'priority': priority}

        #NO TEXTFSM TEMPLATE AVAILABLE FOR OSPF COMMANDS
        neighbors_detail = conn.send_command("show ip ospf ne").split("\n")[2:]
        ospf_detail = conn.send_command("show ip ospf").split("\n")[0]
        if len(ospf_detail) > 1:
            router_id = ospf_detail.split()[-1]
            health_data['ospf']['router_id'] = router_id
            health_data['ospf']['neighbor_count'] = len(neighbors_detail)
            health_data['ospf']['neighbor_details'] = []
            for neighbor in neighbors_detail:
                n_detail = neighbor.split()

                health_data['ospf']['neighbor_details'].append({
                    "neighbor_id": n_detail[0],
                    "status": n_detail[2],
                    "interface": n_detail[-1]
                })
            ospf_interfaces=conn.send_command("show ip ospf int brief",use_textfsm=True)
            health_data['ospf']['net_interfaces'] = {}
            for interface in ospf_interfaces:
                health_data['ospf']['net_interfaces'][normalize_interface_name(interface.get('interface'))]= {'area':int(interface.get('area'))}
            default_info = conn.send_command("show run | section ospf 1 ", use_textfsm=True)
            if 'default-information originate' in default_info:
                health_data['ospf']['default_information']=True


            passive_interfaces=conn.send_command("sh run | section passive-interface ",use_textfsm=True)
            non_passive = re.findall('no passive-interface (.+)', passive_interfaces)
            non=[]
            if non_passive:
                non=[normalize_interface_name(advt_interface) for advt_interface in non_passive]
            health_data['ospf']['advt_interfaces']=non

        standby = conn.send_command("show standby brief", use_textfsm=True)

        for interface in standby:
            if health_data['hsrp'].get(normalize_interface_name(interface.get('interface'))):
                health_data['hsrp'][normalize_interface_name(interface.get('interface'))][interface.get('group')]={
                'state': interface.get('state'),
                'ip': interface.get('virtual_ip_address'),
                'priority':int(interface.get('priority')),
                'Preemption': True if interface.get('preempt') == 'P' else False
            }
            else:
                health_data['hsrp'][normalize_interface_name(interface.get('interface'))] = {}
                health_data['hsrp'][normalize_interface_name(interface.get('interface'))][interface.get('group')]={
                    'state': interface.get('state'),
                    'ip': interface.get('virtual_ip_address'),
                    'priority': int(interface.get('priority')),
                    'Preemption': True if interface.get('preempt') == 'P' else False
                    }
        #NO TEXTFSM TEMPLATE AVAILABLE FOR ETHERCHANNEL COMMANDS
        etherchannel_summary = conn.send_command("show etherc sum ", use_textfsm=True).split("\n")[21:]
        for etherchannel_list in etherchannel_summary:
            etherchannel = etherchannel_list.split()
            if etherchannel:
                health_data['etherchannel'][etherchannel[0]] = {
                    "Portchannel_status": re.search('\((\w+)\)', etherchannel[1]).group(1),
                    "Portchannel_protocol": etherchannel[2],
                    "Portchannel_interfaces": [normalize_interface_name(interface) for interface in etherchannel[3:]]
                }
        conn.disconnect()
        logger.info(f"COLLECTION FOR {device_info} COMPLETE")
        return device_info, health_data
        # all your collection code here
    except Exception as e:
        logger.exception(f"COLLECTION FAILED FOR {device_info}")
        return device_info,{'ERROR':str(e)}

def collector():
    with open("devices.yaml","r") as file:
        device_details = safe_load(file)
    vlan_ids = set()
    health_report = {}

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [
            executor.submit(
                collect_device,
                device,
                device_details['global']
            )
            for device in device_details['devices'].items()
        ]

        for future in futures:
            device_name, data = future.result()
            health_report[device_name] = data


    for device_name in health_report:
        if 'ERROR' not in health_report[device_name]:
            for vlan in health_report[device_name]['stp']:
                vlan_ids.add(vlan)

    for vlan in vlan_ids:
        priority=32768
        root_device=None
        for device in health_report:
            if 'ERROR' not in health_report[device]:
                if vlan in health_report[device]['stp']:
                    if health_report[device]['stp'][vlan]['priority']<priority:
                        priority=health_report[device]['stp'][vlan]['priority']
                        root_device=device
        if root_device:
            health_report[root_device]['stp'][vlan]['role']=True


    snapshot_dir = Path("network_status")
    snapshot_dir.mkdir(exist_ok=True)

    os.chdir("network_status")
    data=json.dumps(health_report,indent=4)
    with open(f"status{str(datetime.now().isoformat()).replace(':','').replace('.','_')}.json","w") as file:
        file.write(data)
    with open("latest.json","w") as file:
        file.write(data)
    os.chdir("..")


#collector()
