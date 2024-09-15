# eventos.py
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
            event_start = parser.isoparse(event['start'])
            event_stop = parser.isoparse(event['stop'])

            # Asegurarse de que las fechas están en UTC
            if event_start.tzinfo is None:
                event_start = mexico_tz.localize(event_start).astimezone(pytz.utc)
            else:
                event_start = event_start.astimezone(pytz.utc)
            
            if event_stop.tzinfo is None:
                event_stop = mexico_tz.localize(event_stop).astimezone(pytz.utc)
            else:
                event_stop = event_stop.astimezone(pytz.utc)

            event.update({
                'start': event_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'stop': event_stop.strftime('%Y-%m-%dT%H:%M:%SZ')
            })

        return jsonify({'status': 'success', 'events': events}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
