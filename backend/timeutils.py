from datetime import datetime,timedelta
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
def valid_timezone(name):
    try: ZoneInfo(name); return True
    except (ZoneInfoNotFoundError,TypeError): return False
def local_today(user): return datetime.now(ZoneInfo(user.timezone)).date().isoformat()
def week_bounds(value):
    d=datetime.strptime(value,"%Y-%m-%d").date()
    sunday=d-timedelta(days=(d.weekday()+1)%7)
    return sunday,sunday+timedelta(days=6)
