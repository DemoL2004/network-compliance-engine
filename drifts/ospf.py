def compare_ospf(expected, current):
    common = set(expected.keys()) & set(current.keys())
    drifts = []
    for key in common:
        if key in ['router_id', 'default_information']:
            if expected.get(key) != current.get(key):
                drifts.append({
                    'type': 'ospf_key_mismatch',
                    'key': key
                })
            continue
        missing_interface = set(expected.get(key)) - set(current.get(key))
        extra_interface = set(current.get(key)) - set(expected.get(key))
        if key == 'net_interfaces':
            for interface in set(expected.get(key)) & set(current.get(key)):
                if expected.get(key).get(interface)['area'] != current.get(key).get(interface)['area']:
                    drifts.append({
                        'type': 'ospf_interface_area_mismatch',
                        'key': key,
                        'interface': interface
                    })

            if missing_interface:
                for interface in missing_interface:
                    drifts.append({
                        'type': 'ospf_interface_missing',
                        'key': key,
                        'interface': interface
                    })
            if extra_interface:
                for interface in extra_interface:
                    drifts.append({
                        'type': 'ospf_interface_extra',
                        'key': key,
                        'interface': interface
                    })
        if key == 'advt_interfaces':
            if missing_interface:
                for interface in missing_interface:
                    drifts.append({
                        'type': 'ospf_advt_interface_missing',
                        'key': key,
                        'interface': interface
                    })
            if extra_interface:
                for interface in extra_interface:
                    drifts.append({
                        'type': 'ospf_advt_interface_extra',
                        'key': key,
                        'interface': interface
                    })
    return drifts
