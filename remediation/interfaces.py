from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))


def build_acl_entry(seq, entry):
    cmd = [
        str(seq),
        entry.get('action'),
        entry.get('packet_type', 'ip'),
        entry.get('source_network')
    ]
    if entry.get('source_wildcard'):
        cmd.append(entry.get('source_wildcard'))
    if entry.get('source_port_comparator'):
        cmd.append(entry.get('source_port_comparator'))
    if entry.get('source_port'):
        cmd.append(str(entry.get('source_port')))
    cmd.append(entry.get('destination_network'))
    if entry.get('destination_wildcard'):
        cmd.append(entry.get('destination_wildcard'))
    if entry.get('destination_port_comparator'):
        cmd.append(entry.get('destination_port_comparator'))
    if entry.get('destination_port'):
        cmd.append(str(entry.get('destination_port')))

    return cmd


def generate_full_interface_remediation(expected_status, interface):
    template = env.get_template('interface.jinja')
    output = template.render(
        interface_data=expected_status,
        interface_id=interface
    )
    return output


def handle_drift_interfaces(drifts, device, device_info, health_report):
    remediate = []
    report = []
    if drifts:
        ip_changed = []
        for drift in drifts:
            if drift['type'] == 'missing_interface':
                report.append({
                    'driftid':f"{device}:MISSING_INTERFACE:{drift['interface']}",
                    'severity': 'ALERT',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"INTERFACE {drift['interface']} MISSING"
                })
                remediate.append({
                    "driftid":f"{device}:MISSING_INTERFACE:{drift['interface']}",
                "commands":generate_full_interface_remediation(device_info['interfaces'][drift['interface']],
                                                                     drift['interface']).split("\n")})
            elif drift['type'] == 'extra_interface':
                report.append({
                    'driftid': f"{device}:EXTRA_INTERFACE:{drift['interface']}",
                    'severity': 'WARNING',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"EXTRA INTERFACE {drift['interface']}"
                })
                remediate.append({
                    "driftid": f"{device}:EXTRA_INTERFACE:{drift['interface']}",
                    "commands": [
                        f"int {drift['interface']}",
                        "shutdown"
                    ]
                })
            elif drift['type'] == 'interface_not_set_to_access':
                report.append({
                    'driftid': f"{device}:INTERFACE_NOT_SET_TO_ACCESS:{drift['interface']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"INTERFACE {drift['interface']} NOT SET TO ACCESS"
                })
                remediate.append({
                    "driftid": f"{device}:INTERFACE_NOT_SET_TO_ACCESS:{drift['interface']}",
                    "commands": [
                        f"int {drift['interface']}",
                        f"switchport access vlan {device_info['interfaces'][drift['interface']]['vlan']}"
                    ]
                })
            elif drift['type'] == 'interface_not_set_to_trunk':
                report.append({
                    'driftid': f"{device}:INTERFACE_NOT_SET_TO_TRUNK:{drift['interface']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"INTERFACE {drift['interface']} NOT SET TO TRUNK"
                })
                remediate.append({
                    "driftid": f"{device}:INTERFACE_NOT_SET_TO_TRUNK:{drift['interface']}",
                    "commands": [
                        f"int {drift['interface']}",
                        f"switchport trunk allowed vlan {','.join(str(x) for x in device_info['interfaces'][drift['interface']]['vlans'])}"
                    ]
                })
            elif drift['type'] == 'interface_down':
                report.append({
                    'driftid': f"{device}:INTERFACE_DOWN:{drift['interface']}",
                    'severity': 'ALERT',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"INTERFACE {drift['interface']} DOWN"
                })
            elif drift['type'] == 'missing_vlans_for_trunk':
                report.append({
                    'driftid': f"{device}:MISSING_VLANS_FOR_TRUNK:{drift['interface']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"MISSING VLANS FOR TRUNK INTERFACE {drift['interface']} {','.join(str(vlan) for vlan in drift['vlans'])}"
                })
                remediate.append({
                    'driftid': f"{device}:MISSING_VLANS_FOR_TRUNK:{drift['interface']}",
                    'commands': [
                        f"int {drift['interface']}",
                        f"switchport trunk allowed vlan add {','.join(str(vlan) for vlan in drift['vlans'])}"
                    ]
                })
            elif drift['type'] == 'extra_vlans_for_trunk':
                report.append({
                    'driftid': f"{device}:EXTRA_VLANS_FOR_TRUNK:{drift['interface']}",
                    'severity': 'WARNING',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"EXTRA VLANS FOR TRUNK INTERFACE {drift['interface']} {','.join(str(vlan) for vlan in drift['vlans'])}"
                })
                remediate.append({
                    'driftid': f"{device}:EXTRA_VLANS_FOR_TRUNK:{drift['interface']}",
                    'commands': [
                        f"int {drift['interface']}",
                        f"switchport trunk allowed vlan remove {','.join(str(vlan) for vlan in drift['vlans'])}"
                    ]
                })
            elif drift['type'] == 'interface_type_mismatch':
                report.append({
                    'driftid': f"{device}:INTERFACE_TYPE_MISMATCH:{drift['interface']}",
                    'severity': 'ALERT',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"INTERFACE {drift['interface']} TYPE CHANGED TO {health_report[device]['interfaces'][drift['interface']]['type']}"
                })
                remediate.append({
                    'driftid': f"{device}:INTERFACE_TYPE_MISMATCH:{drift['interface']}",
                    'commands': generate_full_interface_remediation(
                        device_info['interfaces'][drift['interface']],
                        drift['interface']
                    ).split("\n")
                })
            elif drift['type'] == 'interface_ip_mismatch':
                report.append({
                    'driftid': f"{device}:INTERFACE_IP_MISMATCH:{drift['interface']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"INTERFACE {drift['interface']} IP CHANGED TO {health_report[device]['interfaces'][drift['interface']]['ip']}"
                })
                if drift['interface'] not in ip_changed:
                    remediate.append({
                        'driftid': f"{device}:INTERFACE_IP_MISMATCH:{drift['interface']}",
                        'commands': [
                            f"int {drift['interface']}",
                            f"ip address {device_info['interfaces'][drift['interface']].get('ip')} {device_info['interfaces'][drift['interface']].get('subnet')}"
                        ]
                    })
                    ip_changed.append(drift['interface'])
            elif drift['type'] == 'interface_subnet_mismatch':
                report.append({
                    'driftid': f"{device}:INTERFACE_SUBNET_MISMATCH:{drift['interface']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"INTERFACE {drift['interface']} SUBNET CHANGED TO {health_report[device]['interfaces'][drift['interface']]['subnet']}"
                })
                if drift['interface'] not in ip_changed:
                    remediate.append({
                        'driftid': f"{device}:INTERFACE_SUBNET_MISMATCH:{drift['interface']}",
                        'commands': [
                            f"int {drift['interface']}",
                            f"ip address {device_info['interfaces'][drift['interface']].get('ip')} {device_info['interfaces'][drift['interface']].get('subnet')}"
                        ]
                    })
                    ip_changed.append(drift['interface'])
            elif drift['type'] == 'interface_access_vlan_mismatch':
                report.append({
                    'driftid': f"{device}:INTERFACE_ACCESS_VLAN_MISMATCH:{drift['interface']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"INTERFACE {drift['interface']} ACCESS VLAN CHANGED TO {health_report[device]['interfaces'][drift['interface']]['vlan']}"
                })
                remediate.append({
                    'driftid': f"{device}:INTERFACE_ACCESS_VLAN_MISMATCH:{drift['interface']}",
                    'commands': [
                        f"int {drift['interface']}",
                        f"switchport access vlan {device_info['interfaces'][drift['interface']]['vlan']}"
                    ]
                })
            elif drift['type'] == 'missing_acl_direction':
                report.append({
                    'driftid': f"{device}:MISSING_ACL_DIRECTION:{drift['interface']}:{drift['direction']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"ACL {drift['direction'].upper()} MISSING ON INTERFACE {drift['interface']}"
                })
                template = env.get_template('acl.jinja')
                output = template.render(
                    acl_data=device_info['interfaces'][drift['interface']]['acl'].get(drift['direction'])
                )
                remediate.append({
                    'driftid': f"{device}:MISSING_ACL_DIRECTION:{drift['interface']}:{drift['direction']}",
                    'commands': output.split("\n") + [
                        f"int {drift['interface']}",
                        f"ip access-group {device_info['interfaces'][drift['interface']]['acl'][drift['direction']].get('name')} {drift['direction']}"
                    ]
                })
            elif drift['type'] == 'extra_acl_direction':
                report.append({
                    'driftid': f"{device}:EXTRA_ACL_DIRECTION:{drift['interface']}:{drift['direction']}",
                    'severity': 'WARNING',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"EXTRA ACL {drift['direction'].upper()} ON INTERFACE {drift['interface']}"
                })
                remediate.append({
                    'driftid': f"{device}:EXTRA_ACL_DIRECTION:{drift['interface']}:{drift['direction']}",
                    'commands': [
                        f"int {drift['interface']}",
                        f"no ip access-group {health_report[device]['interfaces'][drift['interface']]['acl'][drift['direction']]['name']} {drift['direction']}"
                    ]
                })
            elif drift['type'] == 'acl_mode_mismatch':
                report.append({
                    'driftid': f"{device}:ACL_MODE_MISMATCH:{drift['interface']}:{drift['direction']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"ACL MODE MISMATCH ON INTERFACE {drift['interface']} {drift['direction'].upper()}"
                })
                template = env.get_template('acl.jinja')
                output = template.render(
                    acl_data=device_info['interfaces'][drift['interface']]['acl'].get(drift['direction'])
                )
                remediate.append({
                    'driftid': f"{device}:ACL_MODE_MISMATCH:{drift['interface']}:{drift['direction']}",
                    'commands': [
                                    f"no ip access-list {health_report[device]['interfaces'][drift['interface']]['acl'][drift['direction']].get('mode')} {health_report[device]['interfaces'][drift['interface']]['acl'][drift['direction']].get('name')}"
                                ] + output.split("\n") + [
                                    f"int {drift['interface']}",
                                    f"ip access-group {device_info['interfaces'][drift['interface']]['acl'][drift['direction']]['name']} {drift['direction']}"
                                ]
                })
            elif drift['type'] == 'acl_name_mismatch':
                report.append({
                    'driftid': f"{device}:ACL_NAME_MISMATCH:{drift['interface']}:{drift['direction']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"ACL NAME MISMATCH ON INTERFACE {drift['interface']} {drift['direction'].upper()}"
                })
                template = env.get_template('acl.jinja')
                output = template.render(
                    acl_data=device_info['interfaces'][drift['interface']]['acl'].get(drift['direction'])
                )
                remediate.append({
                    'driftid': f"{device}:ACL_NAME_MISMATCH:{drift['interface']}:{drift['direction']}",
                    'commands': [
                                    f"no ip access-list {health_report[device]['interfaces'][drift['interface']]['acl'][drift['direction']].get('mode')} {health_report[device]['interfaces'][drift['interface']]['acl'][drift['direction']].get('name')}"
                                ] + output.split("\n") + [
                                    f"int {drift['interface']}",
                                    f"ip access-group {device_info['interfaces'][drift['interface']]['acl'][drift['direction']]['name']} {drift['direction']}"
                                ]
                })
            elif drift['type'] == 'acl_seq_mismatch':
                report.append({
                    'driftid': f"{device}:ACL_SEQ_MISMATCH:{drift['interface']}:{drift['direction']}:{drift['seq']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"ACL SEQUENCE {drift['seq']} MISMATCH ON INTERFACE {drift['interface']} {drift['direction'].upper()}"
                })
                entry = device_info['interfaces'][drift['interface']]['acl'][drift['direction']]['seq'].get(
                    drift['seq']
                )
                remediate.append({
                    'driftid': f"{device}:ACL_SEQ_MISMATCH:{drift['interface']}:{drift['direction']}:{drift['seq']}",
                    'commands': [
                        f"ip access-list {device_info['interfaces'][drift['interface']]['acl'][drift['direction']].get('mode')} {device_info['interfaces'][drift['interface']]['acl'][drift['direction']].get('name')}",
                        f"no {drift['seq']}",
                        " ".join(build_acl_entry(drift['seq'], entry))
                    ]
                })
            elif drift['type'] == 'acl_seq_missing':
                report.append({
                    'driftid': f"{device}:ACL_SEQ_MISSING:{drift['interface']}:{drift['direction']}:{drift['seq']}",
                    'severity': 'ERROR',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"ACL SEQUENCE {drift['seq']} MISSING ON INTERFACE {drift['interface']} {drift['direction'].upper()}"
                })
                entry = device_info['interfaces'][drift['interface']]['acl'][drift['direction']]['seq'].get(
                    drift['seq']
                )
                remediate.append({
                    'driftid': f"{device}:ACL_SEQ_MISSING:{drift['interface']}:{drift['direction']}:{drift['seq']}",
                    'commands': [
                        f"ip access-list {device_info['interfaces'][drift['interface']]['acl'][drift['direction']].get('mode')} {device_info['interfaces'][drift['interface']]['acl'][drift['direction']].get('name')}",
                        " ".join(build_acl_entry(drift['seq'], entry))
                    ]
                })
            elif drift['type'] == 'acl_seq_extra':
                report.append({
                    'driftid': f"{device}:ACL_SEQ_EXTRA:{drift['interface']}:{drift['direction']}:{drift['seq']}",
                    'severity': 'WARNING',
                    'category': 'INTERFACE',
                    'device': device,
                    'message': f"EXTRA ACL SEQUENCE {drift['seq']} ON INTERFACE {drift['interface']} {drift['direction'].upper()}"
                })
                remediate.append({
                    'driftid': f"{device}:ACL_SEQ_EXTRA:{drift['interface']}:{drift['direction']}:{drift['seq']}",
                    'commands': [
                        f"ip access-list {device_info['interfaces'][drift['interface']]['acl'][drift['direction']].get('mode')} {device_info['interfaces'][drift['interface']]['acl'][drift['direction']].get('name')}",
                        f"no {drift['seq']}"
                    ]
                })

    return remediate, report
