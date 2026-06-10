def compare_acl(expected, current, interface):
    missing_acl_direction = set(expected.keys()) - set(current.keys())
    extra_acl_direction = set(current.keys()) - set(expected.keys())
    common_acl_direction = set(expected.keys()) & set(current.keys())
    drifts_for_acl = []
    if missing_acl_direction:
        for direction in missing_acl_direction:
            drifts_for_acl.append({
                'type': 'missing_acl_direction',
                'interface': interface,
                'direction': direction
            })
    if extra_acl_direction:
        for direction in extra_acl_direction:
            drifts_for_acl.append({
                'type': 'extra_acl_direction',
                'interface': interface,
                'direction': direction,
            })
    metadata = ['name', 'mode']
    if common_acl_direction:
        for direction in common_acl_direction:
            acl_rebuilt = False
            for vari in set(expected.get(direction).keys()) & set(current.get(direction).keys()):
                if expected.get(direction).get(vari) != current.get(direction).get(vari):
                    if vari in metadata:
                        drifts_for_acl.append({
                            'type': f'acl_{vari}_mismatch',
                            'interface': interface,
                            'direction': direction
                        })
                        acl_rebuilt = True
                    elif not acl_rebuilt and vari == 'seq':
                        for seq in set(expected.get(direction).get(vari).keys()) & set(
                                current.get(direction).get(vari).keys()):
                            if expected.get(direction).get(vari).get(seq) != current.get(direction).get(vari).get(seq):
                                drifts_for_acl.append({
                                    'type': 'acl_seq_mismatch',
                                    'interface': interface,
                                    'direction': direction,
                                    "seq": seq
                                })

            missing_seq = (set(expected[direction].get('seq').keys()) - set(current[direction].get('seq').keys()))
            if missing_seq:
                for seq in missing_seq:
                    drifts_for_acl.append({
                        'type': 'acl_seq_missing',
                        'interface': interface,
                        'direction': direction,
                        "seq": seq
                    })
            extra_seq = (set(current[direction].get('seq').keys()) - set(expected[direction].get('seq').keys()))
            if extra_seq:
                for seq in extra_seq:
                    drifts_for_acl.append({
                        'type': 'acl_seq_extra',
                        'interface': interface,
                        'direction': direction,
                        "seq": seq
                    })
    return drifts_for_acl
