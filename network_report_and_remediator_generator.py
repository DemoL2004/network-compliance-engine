from yaml import safe_load
import json
from drifts.vlan import compare_vlan
from drifts.interface import compare_interface
from drifts.dhcp import compare_dhcp
from drifts.ospf import compare_ospf
from drifts.hsrp import compare_hsrp
from drifts.etherchannel import compare_etherchannel
import logging
from remediation.vlan import handle_drift_vlan
from remediation.interfaces import handle_drift_interfaces
from remediation.dhcp import handle_drift_dhcp
from remediation.ospf import handle_drift_ospf
from remediation.hsrp import handle_drift_hsrp
from remediation.etherchannel import handle_drift_etherchannel
from datetime import datetime

logger=logging.getLogger("reporter")
def report_and_remediate():
    with open("config/device_configs.yaml", "r") as expected:
        expected_status=safe_load(expected)


    with open("network_status/latest.json","r") as file:
        health_report=json.load(file)

    try:
        with open("remediate_status/drift.json", "r") as file:
            historical_drifts = json.load(file)
    except FileNotFoundError:
        historical_drifts = {}
    report=[]
    all_remediate={}
    all_current_drifts=set()
    for device,device_info in expected_status.get('devices').items():
        logger.info(f"REPORT AND REMEDIATION GENRATION FOR {device} STARTED")
        remediate = []
        if device_info.get('vlans'):
            drifts_vlan=compare_vlan(device_info.get('vlans'),health_report[device].get('vlans'))
            remediate_vlan,report_vlan=handle_drift_vlan(drifts_vlan,device,device_info,health_report)
            remediate.extend(remediate_vlan)
            report.extend(report_vlan)
        portchannel_interfaces=None
        if device_info.get('etherchannel'):
            drifts_etherchannel,portchannel_interfaces=compare_etherchannel(device_info.get('etherchannel'),health_report[device].get('etherchannel'),expected_status['global']['etherchannel']['protocol'])
            remediate_etherchannel,report_etherchannel=handle_drift_etherchannel(drifts_etherchannel,device,device_info)
            remediate.extend(remediate_etherchannel)
            report.extend(report_etherchannel)

        drifts_interface=compare_interface(device_info.get('interfaces'),health_report[device].get('interfaces'),portchannel_interfaces)
        remediate_interface, report_interface = handle_drift_interfaces(drifts_interface, device, device_info,health_report)
        remediate.extend(remediate_interface)
        report.extend(report_interface)

        if device_info.get('dhcp'):
            drifts_dhcp=compare_dhcp(device_info.get('dhcp'),health_report[device].get('dhcp'))
            remediate_dhcp, report_dhcp = handle_drift_dhcp(drifts_dhcp, device, device_info, health_report)
            remediate.extend(remediate_dhcp)
            report.extend(report_dhcp)

        if device_info.get('ospf'):
            drifts_ospf=compare_ospf(device_info.get('ospf'),health_report[device].get('ospf'))
            remediate_ospf, report_ospf = handle_drift_ospf(drifts_ospf, device, device_info, health_report)
            remediate.extend(remediate_ospf)
            report.extend(report_ospf)
        if device_info.get('hsrp'):
            preemption=expected_status.get('global').get('hsrp').get('preemption')
            drifts_hsrp=compare_hsrp(device_info.get('hsrp'),health_report[device].get('hsrp'),preemption)
            remediate_hsrp, report_hsrp = handle_drift_hsrp(drifts_hsrp, device, device_info, preemption)
            remediate.extend(remediate_hsrp)
            report.extend(report_hsrp)

        current_drifts = {drift['driftid'] for drift in remediate} - {f'{device}:OSPF_GLOBAL'}
        all_current_drifts.update(current_drifts)


        cmdlist=[]
        for drift in remediate:
            if historical_drifts.get(drift['driftid'],0)<3 and drift['driftid']!=f'{device}:OSPF_GLOBAL':
                historical_drifts[drift['driftid']]=historical_drifts.get(drift['driftid'],0)+1
                cmdlist.extend(drift['commands'])
            else:
                logger.error(f"MAX REMEDIATION ATTEMPTS REACHED FOR {drift['driftid']}")




        all_remediate[device]=cmdlist
        logger.info(f"REPORT AND REMEDIATION GENRATION FOR {device} DONE")
    for driftid in list(historical_drifts):
        if driftid not in all_current_drifts:
            logger.info(f"DRIFT FIXED FOR DRIFT ID {driftid}")
            del historical_drifts[driftid]
    with open("remediate_status/drift.json","w") as file:
        json.dump(historical_drifts,file,indent=4)
    with open("remediate_status/latest.json", "w") as file:
        json.dump(all_remediate, file, indent=4)
    with open(f"remediate_status/remediate_{str(datetime.now().isoformat()).replace(':','').replace('.','_')}.json", "w") as file:
        json.dump(all_remediate, file, indent=4)
    with open("health_status/health_report.txt", "w") as file:

        file.write("=== NETWORK HEALTH REPORT ===\n\n")

        for event in report:

            file.write(
                f"[{event['driftid']}] "
                f"[{event['severity']}] "
                f"[{event['category']}] "
                f"[{event['device']}] "
                f"{event['message']}\n"
            )
    with open(f"health_status/health_report{str(datetime.now().isoformat()).replace(':','').replace('.','_')}.txt", "w") as file:

        file.write("=== NETWORK HEALTH REPORT ===\n\n")

        for event in report:

            file.write(
                f"[{event['driftid']}] "
                f"[{event['severity']}] "
                f"[{event['category']}] "
                f"[{event['device']}] "
                f"{event['message']}\n"
            )
    with open("health_status/health_report.json", "w") as file:
        json.dump(report, file, indent=4)
    with open(f"health_status/health_report{str(datetime.now().isoformat()).replace(':','').replace('.','_')}.json", "w") as file:
        json.dump(report, file, indent=4)