import pytz
from datetime import datetime

mexico_tz = pytz.timezone('America/Mexico_City')

def local_to_utc(local_time_input):
    # Si ya es un objeto datetime, retornarlo directamente en UTC
    if isinstance(local_time_input, datetime):
        local_time = local_time_input
    else:
        # Si es una cadena, intentamos convertirla
        try:
            # Intentar con formato ISO 8601: 'YYYY-MM-DDTHH:MM:SS'
            local_time = datetime.strptime(local_time_input, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            # Intentar con formato 'YYYY-MM-DD HH:MM:SS'
            local_time = datetime.strptime(local_time_input, '%Y-%m-%d %H:%M:%S')

    # Localizar en la zona horaria de México y convertir a UTC
    local_time = mexico_tz.localize(local_time)
    return local_time.astimezone(pytz.utc)
