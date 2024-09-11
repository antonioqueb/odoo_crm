import pytz
from datetime import datetime

mexico_tz = pytz.timezone('America/Mexico_City')

def local_to_utc(local_time_str):
    try:
        # Intentar con formato ISO 8601: 'YYYY-MM-DDTHH:MM:SS'
        local_time = datetime.strptime(local_time_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        # Intentar con formato 'YYYY-MM-DD HH:MM:SS'
        local_time = datetime.strptime(local_time_str, '%Y-%m-%d %H:%M:%S')
    
    # Localizar en la zona horaria de México y convertir a UTC
    local_time = mexico_tz.localize(local_time)
    return local_time.astimezone(pytz.utc)
