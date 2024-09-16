from flask import jsonify, request
from datetime import datetime
import pytz
from dateutil import parser

def get_events(models, db, uid, password, mexico_tz):
    try:
        # Obtener parámetros de la solicitud
        start_time, end_time, company_id = (
            request.args.get(k) for k in ['start_time', 'end_time', 'company_id']
        )
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")
        
        # Parsear fechas recibidas como UTC (sin conversión adicional)
        start_dt = parser.isoparse(start_time).astimezone(pytz.utc)
        end_dt = parser.isoparse(end_time).astimezone(pytz.utc)

        # Convertir a la zona horaria de México para realizar la consulta en Odoo
        start_dt_mx = start_dt.astimezone(mexico_tz)
        end_dt_mx = end_dt.astimezone(mexico_tz)

        # Formatear fechas para la consulta en Odoo en la zona horaria de México
        start_str = start_dt_mx.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_dt_mx.strftime('%Y-%m-%d %H:%M:%S')

        # Buscar eventos en Odoo usando las fechas en la zona horaria de México
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_str), 
                ('stop', '>=', start_str), 
                ('company_id', '=', int(company_id))
            ]], {'fields': ['start', 'stop']}
        )

        # Convertir fechas de eventos nuevamente a UTC para enviarlas en la respuesta
        for event in events:
            event_start = parser.isoparse(event['start'])
            event_stop = parser.isoparse(event['stop'])

            # Convertir las fechas de la zona horaria de México a UTC
            event_start_utc = mexico_tz.localize(event_start).astimezone(pytz.utc)
            event_stop_utc = mexico_tz.localize(event_stop).astimezone(pytz.utc)

            # Actualizar las fechas sin el sufijo 'Z' para que se mantengan en UTC
            event.update({
                'start': event_start_utc.strftime('%Y-%m-%dT%H:%M:%S'),
                'stop': event_stop_utc.strftime('%Y-%m-%dT%H:%M:%S')
            })

        return jsonify({'status': 'success', 'events': events}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
