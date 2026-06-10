def ospf_net_interfaces_modifier(interface, area, modification):
    if modification == 'add':
        output = [f"int {interface}", f"ip ospf 1 area {area}"]
        return output
    if modification == 'remove':
        output = [f"int {interface}", f"no ip ospf 1 area {area}"]
        return output


def handle_drift_ospf(drifts, device, device_info, health_report):
    remediate = []
    report = []

    if drifts:

        remediate.append({
            'driftid': f"{device}:OSPF_GLOBAL",
            'commands': [
                "router ospf 1"
            ]
        })

        for drift in drifts:

            if drift['type'] == 'ospf_key_mismatch':

                if drift['key'] == "router_id":

                    report.append({
                        'driftid': f"{device}:OSPF_ROUTER_ID_MISMATCH",
                        'severity': 'ERROR',
                        'category': 'OSPF',
                        'device': device,
                        'message': f"OSPF ROUTER ID CHANGED TO {health_report[device]['ospf'].get('router_id')}"
                    })

                    remediate.append({
                        'driftid': f"{device}:OSPF_ROUTER_ID_MISMATCH",
                        'commands': [
                            f"router-id {device_info['ospf'].get(drift['key'])}"
                        ]
                    })

                elif drift['key'] == "default_information":

                    report.append({
                        'driftid': f"{device}:OSPF_DEFAULT_INFORMATION_MISSING",
                        'severity': 'ERROR',
                        'category': 'OSPF',
                        'device': device,
                        'message': "OSPF DEFAULT-INFORMATION ORIGINATE MISSING"
                    })

                    remediate.append({
                        'driftid': f"{device}:OSPF_DEFAULT_INFORMATION_MISSING",
                        'commands': [
                            "default-information originate"
                        ]
                    })

            elif drift['type'] == 'ospf_interface_area_mismatch':

                report.append({
                    'driftid': f"{device}:OSPF_INTERFACE_AREA_MISMATCH:{drift['interface']}",
                    'severity': 'ERROR',
                    'category': 'OSPF',
                    'device': device,
                    'message': f"OSPF AREA MISMATCH ON INTERFACE {drift['interface']}"
                })

                remediate.append({
                    'driftid': f"{device}:OSPF_INTERFACE_AREA_MISMATCH:{drift['interface']}",
                    'commands':
                        ospf_net_interfaces_modifier(
                            drift['interface'],
                            health_report[device]['ospf'][drift['key']][drift['interface']]['area'],
                            'remove'
                        )
                        +
                        ospf_net_interfaces_modifier(
                            drift['interface'],
                            device_info['ospf'][drift['key']][drift['interface']]['area'],
                            'add'
                        )
                })

            elif drift['type'] == 'ospf_interface_missing':

                report.append({
                    'driftid': f"{device}:OSPF_INTERFACE_MISSING:{drift['interface']}",
                    'severity': 'ALERT',
                    'category': 'OSPF',
                    'device': device,
                    'message': f"OSPF INTERFACE {drift['interface']} MISSING"
                })

                remediate.append({
                    'driftid': f"{device}:OSPF_INTERFACE_MISSING:{drift['interface']}",
                    'commands': ospf_net_interfaces_modifier(
                        drift['interface'],
                        device_info['ospf'][drift['key']][drift['interface']]['area'],
                        'add'
                    )
                })

            elif drift['type'] == 'ospf_interface_extra':

                report.append({
                    'driftid': f"{device}:OSPF_INTERFACE_EXTRA:{drift['interface']}",
                    'severity': 'WARNING',
                    'category': 'OSPF',
                    'device': device,
                    'message': f"EXTRA OSPF INTERFACE {drift['interface']}"
                })

                remediate.append({
                    'driftid': f"{device}:OSPF_INTERFACE_EXTRA:{drift['interface']}",
                    'commands': ospf_net_interfaces_modifier(
                        drift['interface'],
                        health_report[device]['ospf'][drift['key']][drift['interface']]['area'],
                        'remove'
                    )
                })

            elif drift['type'] == 'ospf_advt_interface_missing':

                report.append({
                    'driftid': f"{device}:OSPF_ADVERTISEMENT_DISABLED:{drift['interface']}",
                    'severity': 'ERROR',
                    'category': 'OSPF',
                    'device': device,
                    'message': f"OSPF ADVERTISEMENT DISABLED ON INTERFACE {drift['interface']}"
                })

                remediate.append({
                    'driftid': f"{device}:OSPF_ADVERTISEMENT_DISABLED:{drift['interface']}",
                    'commands': [
                        "router ospf 1",
                        f"no passive-interface {drift['interface']}"
                    ]
                })

            elif drift['type'] == 'ospf_advt_interface_extra':

                report.append({
                    'driftid': f"{device}:OSPF_ADVERTISEMENT_ENABLED:{drift['interface']}",
                    'severity': 'WARNING',
                    'category': 'OSPF',
                    'device': device,
                    'message': f"OSPF ADVERTISEMENT ENABLED ON UNEXPECTED INTERFACE {drift['interface']}"
                })

                remediate.append({
                    'driftid': f"{device}:OSPF_ADVERTISEMENT_ENABLED:{drift['interface']}",
                    'commands': [
                        "router ospf 1",
                        f"passive-interface {drift['interface']}"
                    ]
                })

    return remediate, report