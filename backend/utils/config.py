DERIVED_VER_KEY = "ver:derived:data"
ALGO_VER_KEY = "ver:derived:algo"

# Change these version numbers anytime to invalidate cache
DERIVED_DATA_VERSION = "1"
ALGO_VERSION = "1"

def get_version(key):
    if key == DERIVED_VER_KEY:
        return DERIVED_DATA_VERSION
    elif key == ALGO_VER_KEY:
        return ALGO_VERSION
    return "1"

def get_versioned_cache_key(endpoint, args):
    derived_ver = get_version(DERIVED_VER_KEY)
    algo_ver = get_version(ALGO_VER_KEY)
    param_str = "&".join(f"{k}={v}" for k, v in sorted(args.items()))
    return f"{endpoint}:{param_str}:data_ver={derived_ver}:algo_ver={algo_ver}"