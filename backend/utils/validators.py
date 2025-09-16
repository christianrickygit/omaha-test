from datetime import datetime

def is_valid_int(val):
    """
    Returns True if val is a positive integer, else False.
    """
    try:
        return val is not None and str(val).strip() != "" and int(val) > 0
    except (ValueError, TypeError):
        return False

def is_valid_date(val):
    """
    Returns True if val matches YYYY-MM-DD format, else False.
    """
    try:
        datetime.strptime(val, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False
    
def is_valid_date_range(start_date, end_date):
    try:
        if not (is_valid_date(start_date) and is_valid_date(end_date)):
            return False
        return datetime.strptime(end_date, "%Y-%m-%d") >= datetime.strptime(start_date, "%Y-%m-%d")
    except Exception:
        return False