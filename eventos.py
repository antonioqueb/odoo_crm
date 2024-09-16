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
        
        # Parsear fechas recibidas como UTC
        start_dt = parser.isoparse(start_time)
        end_dt = parser.isoparse(end_time)

        # Asegurarse de que las fechas están en UTC
        if start_dt.tzinfo is None:
            start_dt = pytz.utc.localize(start_dt)
        else:
            start_dt = start_dt.astimezone(pytz.utc)
        
        if end_dt.tzinfo is None:
            end_dt = pytz.utc.localize(end_dt)
        else:
            end_dt = end_dt.astimezone(pytz.utc)

        # Formatear fechas para la consulta en Odoo en UTC
        start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')

        # Buscar eventos en Odoo usando las fechas en UTC
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_str), 
                ('stop', '>=', start_str), 
                ('company_id', '=', int(company_id))
            ]], {'fields': ['start', 'stop']}
        )

        # Convertir fechas de eventos a UTC
        for event in events:
            event_start = parser.isoparse(event['start'])
            event_stop = parser.isoparse(event['stop'])

            # Asegurarse de que las fechas están en UTC
            if event_start.tzinfo is None:
                event_start = pytz.utc.localize(event_start)
            else:
                event_start = event_start.astimezone(pytz.utc)
            
            if event_stop.tzinfo is None:
                event_stop = pytz.utc.localize(event_stop)
            else:
                event_stop = event_stop.astimezone(pytz.utc)

            # Actualizar las fechas sin el sufijo 'Z' para que se mantengan en UTC
            event.update({
                'start': event_start.strftime('%Y-%m-%dT%H:%M:%S'),
                'stop': event_stop.strftime('%Y-%m-%dT%H:%M:%S')
            })

        return jsonify({'status': 'success', 'events': events}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
