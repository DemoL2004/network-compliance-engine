def compare_hsrp(expected, current, preemption):
    missing = set(expected.keys()) - set(current.keys())
    extra = set(current.keys()) - set(expected.keys())
    common = set(expected.keys()) & set(current.keys())
    drifts = []
    for vlan in common:
        missing_group = set(expected.get(vlan).keys()) - set(current.get(vlan).keys())
        extra_group = set(current.get(vlan).keys()) - set(expected.get(vlan).keys())
        common_group = set(current.get(vlan).keys()) & set(expected.get(vlan).keys())

        for group in common_group:
            if current.get(vlan).get(group).get('Preemption') != preemption:
                drifts.append({
                    'type': 'hsrp_group_preemption_mismatch',
                    'interface': vlan,
                    'group': group
                })
            if expected.get(vlan).get(group).get('ip') != current.get(vlan).get(group).get('ip'):
                drifts.append({
                    'type': 'hsrp_group_ip_mismatch',
                    'interface': vlan,
                    'group': group
                })

        if missing_group:
            for group in missing_group:
                drifts.append({
                    'type': 'hsrp_group_missing',
                    'interface': vlan,
                    'group': group
                })

        if extra_group:
            for group in extra_group:
                drifts.append({
                    'type': 'hsrp_group_extra',
                    'interface': vlan,
                    'group': group
                })

    if missing:
        for vlan in missing:
            for group in expected[vlan]:
                drifts.append({
                    'type': 'hsrp_group_missing',
                    'interface': vlan,
                    'group': group
                })

    if extra:
        for vlan in extra:
            for group in current[vlan]:
                drifts.append({
                    'type': 'hsrp_group_extra',
                    'interface': vlan,
                    'group': group
                })
    return drifts
