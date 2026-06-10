def interface_etherchannel_modifier(etherchannel, interface, mode, modification):
    if modification == 'add':
        output = [f"int {interface}", f"channel-group {etherchannel} mode {mode}"]
        return output
    if modification == 'remove':
        output = [f"int {interface}", f"no channel-group {etherchannel} "]
        return output


def handle_drift_etherchannel(drifts, device, device_info):
    remediate = []
    report = []

    if drifts:
        for drift in drifts:

            if drift['type'] == 'missing_portchannel_interface':
                report.append({
                    'driftid': f"{device}:MISSING_PORTCHANNEL_INTERFACE:{drift['portchannel']}:{drift['interface']}",
                    'severity': 'WARNING',
                    'category': 'ETHERCHANNEL',
                    'device': device,
                    'message': f"PORTCHANNEL {drift['portchannel']} INTERFACE {drift['interface']} MISSING"
                })

                remediate.append({
                    'driftid': f"{device}:MISSING_PORTCHANNEL_INTERFACE:{drift['portchannel']}:{drift['interface']}",
                    'commands': interface_etherchannel_modifier(
                        drift['portchannel'],
                        drift['interface'],
                        device_info['etherchannel'][drift['portchannel']]['mode'],
                        'add'
                    )
                })

            elif drift['type'] == 'extra_portchannel_interface':
                report.append({
                    'driftid': f"{device}:EXTRA_PORTCHANNEL_INTERFACE:{drift['portchannel']}:{drift['interface']}",
                    'severity': 'WARNING',
                    'category': 'ETHERCHANNEL',
                    'device': device,
                    'message': f"PORTCHANNEL {drift['portchannel']} EXTRA INTERFACE {drift['interface']}"
                })

                remediate.append({
                    'driftid': f"{device}:EXTRA_PORTCHANNEL_INTERFACE:{drift['portchannel']}:{drift['interface']}",
                    'commands': interface_etherchannel_modifier(
                        drift['portchannel'],
                        drift['interface'],
                        device_info['etherchannel'][drift['portchannel']]['mode'],
                        'remove'
                    )
                })

            elif drift['type'] == 'missing_portchannel':
                report.append({
                    'driftid': f"{device}:MISSING_PORTCHANNEL:{drift['portchannel']}",
                    'severity': 'ALERT',
                    'category': 'ETHERCHANNEL',
                    'device': device,
                    'message': f"PORTCHANNEL {drift['portchannel']} MISSING "
                })

                commands = []

                for interface in device_info['etherchannel'][drift['portchannel']]['interfaces']:
                    commands.extend(
                        interface_etherchannel_modifier(
                            drift['portchannel'],
                            interface,
                            device_info['etherchannel'][drift['portchannel']]['mode'],
                            'add'
                        )
                    )

                remediate.append({
                    'driftid': f"{device}:MISSING_PORTCHANNEL:{drift['portchannel']}",
                    'commands': commands
                })

            elif drift['type'] == 'extra_portchannel':
                report.append({
                    'driftid': f"{device}:EXTRA_PORTCHANNEL:{drift['portchannel']}",
                    'severity': 'WARNING',
                    'category': 'ETHERCHANNEL',
                    'device': device,
                    'message': f"EXTRA PORTCHANNEL {drift['portchannel']}"
                })

                remediate.append({
                    'driftid': f"{device}:EXTRA_PORTCHANNEL:{drift['portchannel']}",
                    'commands': [
                        f"no interface port-channel{drift['portchannel']}"
                    ]
                })

            elif drift['type'] == 'portchannel_down':
                report.append({
                    'driftid': f"{device}:PORTCHANNEL_DOWN:{drift['portchannel']}",
                    'severity': 'ALERT',
                    'category': 'ETHERCHANNEL',
                    'device': device,
                    'message': f"PORTCHANNEL {drift['portchannel']} IS DOWN"
                })

            elif drift['type'] == 'portchannel_protocol_changed':
                report.append({
                    'driftid': f"{device}:PORTCHANNEL_PROTOCOL_CHANGED:{drift['portchannel']}",
                    'severity': 'ALERT',
                    'category': 'ETHERCHANNEL',
                    'device': device,
                    'message': f"PORTCHANNEL {drift['portchannel']} PROTOCOL CHANGED TO {drift['protocol']}"
                })

    return remediate, report