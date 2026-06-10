def handle_drift_vlan(drifts, device, device_info, health_report):
    remediate = []
    report = []

    if drifts:
        vlan_name_mis = set()

        for drift in drifts:
            expected_vlan = device_info['vlans'].get(drift['vlan'])
            current_vlan = health_report[device]['vlans'].get(drift['vlan'])

            if drift['type'] == 'missing_vlan':

                remediate.append({
                    'driftid': f"{device}:MISSING_VLAN:{drift['vlan']}",
                    'commands': [
                        f"vlan {drift['vlan']}",
                        f"name {expected_vlan['name']}"
                    ]
                })

                report.append({
                    'driftid': f"{device}:MISSING_VLAN:{drift['vlan']}",
                    'severity': 'ERROR',
                    'category': 'VLAN',
                    'device': device,
                    'message': f"MISSING VLAN {drift['vlan']}"
                })

            elif drift['type'] == 'extra_vlan':

                remediate.append({
                    'driftid': f"{device}:EXTRA_VLAN:{drift['vlan']}",
                    'commands': [
                        f"no vlan {drift['vlan']}"
                    ]
                })

                report.append({
                    'driftid': f"{device}:EXTRA_VLAN:{drift['vlan']}",
                    'severity': 'NOTIFICATION',
                    'category': 'VLAN',
                    'device': device,
                    'message': f"EXTRA VLAN {drift['vlan']}"
                })

            elif drift['type'] == 'vlan_name_mismatch':

                remediate.append({
                    'driftid': f"{device}:VLAN_NO_NAME:{drift['vlan']}",
                    'commands': [
                        f"vlan {drift['vlan']}",
                        "no name"
                    ]
                })

                vlan_name_mis.add(drift['vlan'])

                report.append({
                    'driftid': f"{device}:VLAN_NAME_CHANGE:{drift['vlan']}",
                    'severity': 'WARNING',
                    'category': 'VLAN',
                    'device': device,
                    'message': f"VLAN NAME CHANGED TO {current_vlan['name']}"
                })

        for vlan in vlan_name_mis:
            expected_vlan = device_info['vlans'].get(vlan)

            remediate.append({
                'driftid': f"{device}:VLAN_NAME_CHANGE:{vlan}",
                'commands': [
                    f"vlan {vlan}",
                    f"name {expected_vlan['name']}"
                ]
            })

    return remediate, report