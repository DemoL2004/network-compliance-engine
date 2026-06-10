def compare_vlan(expected, current):
    missing = set(expected.keys()) - set(current.keys())
    extra = set(current.keys()) - set(expected.keys())
    common = set(expected.keys()) & set(current.keys())
    drifts = []
    if common:
        for vlan in common:
            if expected[vlan] != current[vlan]:
                drifts.append({
                    'type': 'vlan_name_mismatch',
                    'vlan': vlan
                })

    if extra:
        for vlan in extra:
            drifts.append({
                'type': 'extra_vlan',
                'vlan': vlan
            })
    if missing:
        for vlan in missing:
            drifts.append({
                'type': 'missing_vlan',
                'vlan': vlan
            })
    return drifts
