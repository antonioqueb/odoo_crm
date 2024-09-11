import pytz
from datetime import datetime

mexico_tz = pytz.timezone('America/Mexico_City')

def local_to_utc(local_time_input):
    # Si el input ya es un objeto datetime, no hacer nada
    if isinstance(local_time_input, datetime):
        local_time = local_time_input
    else:
        # Si es una cadena, intentar con formato ISO 8601: 'YYYY-MM-DDTHH:MM:SS'
        try:
            local_time = datetime.strptime(local_time_input, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            # Si falla, intentar con formato 'YYYY-MM-DD HH:MM:SS'
            local_time = datetime.strptime(local_time_input, '%Y-%m-%d %H:%M:%S')
    
    # Localizar en la zona horaria de México y convertir a UTC
    local_time = mexico_tz.localize(local_time)
    return local_time.astimezone(pytz.utc)
