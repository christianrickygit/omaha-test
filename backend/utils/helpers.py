def clear_old_versioned_cache_keys(cache):
    """
    Remove cache keys with outdated version numbers.
    Only works for SimpleCache (in-memory dict).
    """
    from utils.config import DERIVED_DATA_VERSION, ALGO_VERSION
    cache_dict = cache.cache._cache  # SimpleCache internal dict
    current_data_ver = str(DERIVED_DATA_VERSION)
    current_algo_ver = str(ALGO_VERSION)
    keys_to_delete = []
    for key in cache_dict.keys():
        if "data_ver=" in key or "algo_ver=" in key:
            parts = key.split(":")
            for part in parts:
                if part.startswith("data_ver="):
                    ver = part.split("=")[1]
                    if ver < current_data_ver:
                        keys_to_delete.append(key)
                        break
                if part.startswith("algo_ver="):
                    ver = part.split("=")[1]
                    if ver < current_algo_ver:
                        keys_to_delete.append(key)
                        break
    for key in keys_to_delete:
        cache.delete(key)

def clear_forever_cache_keys(cache):
    """
    Delete forever cache keys before data ingestion.
    """
    cache.delete("locations")
    cache.delete("metrics")

def is_valid_id(val):
    """
    Check if the given value is a valid positive integer for use as a primary key.
    """
    try:
        return val is not None and str(val).strip() != "" and int(val) > 0
    except (ValueError, TypeError):
        return False