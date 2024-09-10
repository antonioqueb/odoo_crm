import pytz
from datetime import datetime

mexico_tz = pytz.timezone('America/Mexico_City')

def local_to_utc(local_time_str, fmt='%Y-%m-%d %H:%M:%S'):
    local_time = mexico_tz.localize(datetime.strptime(local_time_str, fmt))
    return local_time.astimezone(pytz.utc)
