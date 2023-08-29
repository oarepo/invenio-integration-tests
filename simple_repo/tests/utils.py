def _get_paths(cur_path, cur_val):
    ret_paths = []
    if isinstance(cur_val, list):
        return ret_paths
    elif isinstance(cur_val, dict):
        for k, v in cur_val.items():
            ret_paths += get_paths(f"{cur_path}.{k}", v)
    else:
        if cur_path.startswith("."):
            cur_path = cur_path[1:]
        ret_paths.append(f"{cur_path}")
    return ret_paths


def get_paths(prefix, data):
    return _get_paths(prefix, data)
