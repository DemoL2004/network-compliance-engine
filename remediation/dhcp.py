def handle_drift_dhcp(drifts, device, device_info, health_report):
    remediate = []
    report = []
    if drifts:
        net_conf = set()
        for drift in drifts:
            if drift['type'] == 'dhcp_pool_missing':
                report.append({
                    'driftid': f"{device}:DHCP_POOL_MISSING:{drift['pool']}",
                    'severity': 'ALERT',
                    'category': 'DHCP',
                    'device': device,
                    'message': f"DHCP POOL {drift['pool']} MISSING"
                })
                remediate.append({
                    'driftid': f"{device}:DHCP_POOL_MISSING:{drift['pool']}",
                    'commands': [
                        f"ip dhcp pool {drift['pool']}",
                        f"network {device_info['dhcp'][drift['pool']].get('ip')} {device_info['dhcp'][drift['pool']].get('subnet')}",
                        f"default-router {device_info['dhcp'][drift['pool']].get('default_gateway')}"
                    ]
                })

            elif drift['type'] == 'dhcp_pool_extra':
                report.append({
                    'driftid': f"{device}:DHCP_POOL_EXTRA:{drift['pool']}",
                    'severity': 'WARNING',
                    'category': 'DHCP',
                    'device': device,
                    'message': f"EXTRA DHCP POOL {drift['pool']}"
                })
                remediate.append({
                    'driftid': f"{device}:DHCP_POOL_EXTRA:{drift['pool']}",
                    'commands': [
                        f"no ip dhcp pool {drift['pool']}"
                    ]
                })

            elif drift['type'] == 'extra_key':
                report.append({
                    'driftid': f"{device}:DHCP_EXTRA_KEY:{drift['pool']}:{drift['key']}",
                    'severity': 'WARNING',
                    'category': 'DHCP',
                    'device': device,
                    'message': f"EXTRA DHCP PARAMETER {drift['key']} IN POOL {drift['pool']}"
                })
                remediate.append({
                    'driftid': f"{device}:DHCP_EXTRA_KEY:{drift['pool']}:{drift['key']}",
                    'commands': [
                        f"ip dhcp pool {drift['pool']}",
                        f"no {drift['key']}"
                    ]
                })

            elif drift['type'] == 'missing_key':
                report.append({
                    'driftid': f"{device}:DHCP_MISSING_KEY:{drift['pool']}:{drift['key']}",
                    'severity': 'ERROR',
                    'category': 'DHCP',
                    'device': device,
                    'message': f"DHCP PARAMETER {drift['key']} MISSING IN POOL {drift['pool']}"
                })

                commands = [f"ip dhcp pool {drift['pool']}"]

                if drift['key'] in ['ip', 'subnet'] and drift['pool'] not in net_conf:
                    commands.append(
                        f"network {device_info['dhcp'][drift['pool']].get('ip')} {device_info['dhcp'][drift['pool']].get('subnet')}"
                    )
                    net_conf.add(drift['pool'])

                if drift['key'] == 'default_gateway':
                    commands.append(
                        f"default-router {device_info['dhcp'][drift['pool']].get('default_gateway')}"
                    )

                remediate.append({
                    'driftid': f"{device}:DHCP_MISSING_KEY:{drift['pool']}:{drift['key']}",
                    'commands': commands
                })

            elif drift['type'] == 'key_mismatch':
                report.append({
                    'driftid': f"{device}:DHCP_KEY_MISMATCH:{drift['pool']}:{drift['key']}",
                    'severity': 'ERROR',
                    'category': 'DHCP',
                    'device': device,
                    'message': f"DHCP PARAMETER {drift['key']} MISMATCH IN POOL {drift['pool']}"
                })

                commands = [f"ip dhcp pool {drift['pool']}"]

                if drift['key'] in ['ip', 'subnet'] and drift['pool'] not in net_conf:
                    commands.extend([
                        f"no network {health_report[device]['dhcp'][drift['pool']].get('ip')} {health_report[device]['dhcp'][drift['pool']].get('subnet')}",
                        f"network {device_info['dhcp'][drift['pool']].get('ip')} {device_info['dhcp'][drift['pool']].get('subnet')}"
                    ])
                    net_conf.add(drift['pool'])

                if drift['key'] == 'default_gateway':
                    commands.extend([
                        f"no default-router {health_report[device]['dhcp'][drift['pool']].get('default_gateway')}",
                        f"default-router {device_info['dhcp'][drift['pool']].get('default_gateway')}"
                    ])

                remediate.append({
                    'driftid': f"{device}:DHCP_KEY_MISMATCH:{drift['pool']}:{drift['key']}",
                    'commands': commands
                })

    return remediate, report