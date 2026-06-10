def handle_drift_hsrp(drifts, device, device_info, preemption):
    remediate = []
    report = []

    if drifts:
        for drift in drifts:

            if drift['type'] == 'hsrp_group_preemption_mismatch':
                report.append({
                    'driftid': f"{device}:HSRP_GROUP_PREEMPTION_MISMATCH:{drift['interface']}:{drift['group']}",
                    'severity': 'ERROR',
                    'category': 'HSRP',
                    'device': device,
                    'message': f"HSRP GROUP {drift['group']} PREEMPTION MISMATCH ON INTERFACE {drift['interface']}"
                })

                remediate.append({
                    'driftid': f"{device}:HSRP_GROUP_PREEMPTION_MISMATCH:{drift['interface']}:{drift['group']}",
                    'commands': [
                        f"int {drift['interface']}",
                        f"{'' if preemption else 'no '}standby {drift['group']} preempt"
                    ]
                })

            elif drift['type'] == 'hsrp_group_ip_mismatch':
                report.append({
                    'driftid': f"{device}:HSRP_GROUP_IP_MISMATCH:{drift['interface']}:{drift['group']}",
                    'severity': 'ERROR',
                    'category': 'HSRP',
                    'device': device,
                    'message': f"HSRP GROUP {drift['group']} VIP CHANGED ON INTERFACE {drift['interface']}"
                })

                remediate.append({
                    'driftid': f"{device}:HSRP_GROUP_IP_MISMATCH:{drift['interface']}:{drift['group']}",
                    'commands': [
                        f"int {drift['interface']}",
                        f"standby {drift['group']} ip {device_info['hsrp'][drift['interface']][drift['group']].get('ip')}"
                    ]
                })

            elif drift['type'] == 'hsrp_group_missing':
                report.append({
                    'driftid': f"{device}:HSRP_GROUP_MISSING:{drift['interface']}:{drift['group']}",
                    'severity': 'ALERT',
                    'category': 'HSRP',
                    'device': device,
                    'message': f"HSRP GROUP {drift['group']} MISSING ON INTERFACE {drift['interface']}"
                })

                commands = [
                    f"int {drift['interface']}",
                    f"standby {drift['group']} ip {device_info['hsrp'][drift['interface']][drift['group']].get('ip')}",
                    f"{'' if preemption else 'no '}standby {drift['group']} preempt"
                ]

                if device_info['hsrp'][drift['interface']][drift['group']]['role'] == 'primary':
                    commands.append(
                        f"standby {drift['group']} priority 110"
                    )

                remediate.append({
                    'driftid': f"{device}:HSRP_GROUP_MISSING:{drift['interface']}:{drift['group']}",
                    'commands': commands
                })

            elif drift['type'] == 'hsrp_group_extra':
                report.append({
                    'driftid': f"{device}:HSRP_GROUP_EXTRA:{drift['interface']}:{drift['group']}",
                    'severity': 'WARNING',
                    'category': 'HSRP',
                    'device': device,
                    'message': f"EXTRA HSRP GROUP {drift['group']} ON INTERFACE {drift['interface']}"
                })

                remediate.append({
                    'driftid': f"{device}:HSRP_GROUP_EXTRA:{drift['interface']}:{drift['group']}",
                    'commands': [
                        f"int {drift['interface']}",
                        f"no standby {drift['group']}"
                    ]
                })

    return remediate, report