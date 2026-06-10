from drifts.acl import compare_acl


def compare_interface(expected, current, portchannel_interfaces):
    missing = set(expected.keys()) - set(current.keys())
    if portchannel_interfaces:
        extra = set(current.keys()) - set(expected.keys()) - set(portchannel_interfaces)
    else:
        extra = set(current.keys()) - set(expected.keys())
    common = set(expected.keys()) & set(current.keys())
    drifts = []
    if missing:
        for interface in missing:
            drifts.append({
                'type': 'missing_interface',
                'interface': interface
            })
    if extra:
        for interface in extra:
            drifts.append({
                'type': 'extra_interface',
                'interface': interface
            })

    for interface in common:
        expected_details = expected[interface]
        current_details = current[interface]
        missing_keys = set(expected_details.keys()) - set(current_details.keys())
        if 'vlan' in missing_keys:
            drifts.append({
                'type': 'interface_not_set_to_access',
                'interface': interface
            })
        if 'vlans' in missing_keys:
            drifts.append({
                'type': 'interface_not_set_to_trunk',
                'interface': interface
            })
        if current_details.get('status') and current_details.get('status') != 'up':
            drifts.append({
                'type': 'interface_down',
                'interface': interface
            })
        for key in (set(expected_details.keys()) & (set(current_details.keys()) - {'status'})):
            if key == 'vlans':
                missing_interface_key = set(expected_details.get(key)) - set(current_details.get(key))
                extra_interface_key = set(current_details.get(key)) - set(expected_details.get(key))
                if missing_interface_key:
                    drifts.append({
                        'type': 'missing_vlans_for_trunk',
                        'interface': interface,
                        'vlans': missing_interface_key
                    })
                if extra_interface_key:
                    drifts.append({
                        'type': 'extra_vlans_for_trunk',
                        'interface': interface,
                        'vlans': extra_interface_key
                    })
                continue
            if key == 'acl':
                drifts.extend(compare_acl(expected_details.get('acl'), current_details.get('acl'), interface))
                continue
            if expected_details.get(key) != current_details.get(key):
                if key == 'type':
                    drifts.append({
                        'type': 'interface_type_mismatch',
                        'interface': interface
                    })
                if key == 'ip':
                    drifts.append({
                        'type': 'interface_ip_mismatch',
                        'interface': interface
                    })
                if key == 'subnet':
                    drifts.append({
                        'type': 'interface_subnet_mismatch',
                        'interface': interface
                    })
                if key == 'vlan':
                    drifts.append({
                        'type': 'interface_access_vlan_mismatch',
                        'interface': interface
                    })

    return drifts
