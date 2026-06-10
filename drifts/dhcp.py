def compare_dhcp(expected, current):
    missing = set(expected.keys()) - set(current.keys())
    extra = set(current.keys()) - set(expected.keys())
    common = set(expected.keys()) & set(current.keys())
    drifts = []
    if missing:
        for pool in missing:
            drifts.append({
                'type': 'dhcp_pool_missing',
                'pool': pool
            })
    if extra:
        for pool in extra:
            drifts.append({
                'type': 'dhcp_pool_extra',
                'pool': pool
            })

    for pool in common:
        missing_key = set(expected.get(pool)) - set(current.get(pool))
        extra_key = set(current.get(pool)) - set(expected.get(pool))
        if extra_key:
            for key in extra_key:
                drifts.append({
                    'type': 'extra_key',
                    'pool': pool,
                    'key': key
                })
        if missing_key:
            for key in missing_key:
                drifts.append({
                    'type': 'missing_key',
                    'pool': pool,
                    'key': key
                })
        common_key = set(expected.get(pool)) & set(current.get(pool))
        for key in common_key:
            if expected.get(pool).get(key) != current.get(pool).get(key):
                drifts.append({
                    'type': 'key_mismatch',
                    'pool': pool,
                    'key': key
                })
    return drifts
