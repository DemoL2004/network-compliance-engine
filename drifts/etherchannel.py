def compare_etherchannel(expected, current, protocol):
    missing = set(expected.keys()) - set(current.keys())
    extra = set(current.keys()) - set(expected.keys())
    common = set(expected.keys()) & set(current.keys())
    drifts = []
    if common:
        for portchannel in common:
            if "U" not in current[portchannel]['Portchannel_status']:
                drifts.append({
                    'type': 'portchannel_down',
                    'portchannel': portchannel
                })
            if protocol != current[portchannel]['Portchannel_protocol']:
                drifts.append({
                    'type': 'portchannel_protocol_changed',
                    'portchannel': portchannel,
                    'protocol': current[portchannel]['Portchannel_protocol']
                })
            expected_int = set(expected[portchannel]['interfaces'])
            current_int = {interface.split('(')[0] for interface in current[portchannel]['Portchannel_interfaces']}
            missing_int = expected_int - current_int
            extra_int = current_int - expected_int
            if missing_int:
                for interface in missing_int:
                    drifts.append({
                        'type': 'missing_portchannel_interface',
                        'portchannel': portchannel,
                        'interface': interface
                    })
            if extra_int:
                for interface in extra_int:
                    drifts.append({
                        'type': 'extra_portchannel_interface',
                        'portchannel': portchannel,
                        'interface': interface
                    })

    if missing:
        for portchannel in missing:
            drifts.append({
                'type': 'missing_portchannel',
                'portchannel': portchannel
            })
            for interface in expected[portchannel]['interfaces']:
                drifts.append({
                    'type': 'missing_portchannel_interface',
                    'portchannel': portchannel,
                    'interface': interface
                })
    if extra:
        for portchannel in extra:
            drifts.append({
                'type': 'extra_portchannel',
                'portchannel': portchannel,
            })
    portchannel_interfaces = []
    for portchannel in expected.keys():
        portchannel_interfaces.extend(expected[portchannel]['interfaces'])
    return drifts, portchannel_interfaces
