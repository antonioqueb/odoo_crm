# eventos.py
from flask import jsonify, request
from datetime import datetime
import pytz

def get_events(models, db, uid, password, mexico_tz):
    try:
        # Obtener parámetros de la solicitud
        start_time, end_time, company_id = (
            request.args.get(k) for k in ['start_time', 'end_time', 'company_id']
        )
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")
        
        # Parsear fechas recibidas como UTC
        start_dt = pytz.utc.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ'))
        end_dt = pytz.utc.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ'))

        # Convertir a la zona horaria de México
        start_dt_mx = start_dt.astimezone(mexico_tz)
        end_dt_mx = end_dt.astimezone(mexico_tz)

        # Formatear fechas para la consulta en Odoo
        start_str = start_dt_mx.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_dt_mx.strftime('%Y-%m-%d %H:%M:%S')

        # Buscar eventos en Odoo
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_str), 
                ('stop', '>=', start_str), 
                ('company_id', '=', int(company_id))
            ]], {'fields': ['start', 'stop']}
        )

        # Convertir fechas de eventos a UTC con el sufijo 'Z'
        for event in events:
            event_start_utc = mexico_tz.localize(datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc)
            event_stop_utc = mexico_tz.localize(datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc)
            event.update({
                'start': event_start_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'stop': event_stop_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            })

        return jsonify({'status': 'success', 'events': events}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
