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
        
        # Parsear fechas recibidas y convertirlas a UTC directamente
        start_dt = parser.isoparse(start_time).astimezone(pytz.utc)
        end_dt = parser.isoparse(end_time).astimezone(pytz.utc)

        # Convertir las fechas a cadena en formato UTC para la consulta en Odoo
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

        # Convertir las fechas de eventos de UTC a la zona horaria de México
        for event in events:
            event_start = parser.isoparse(event['start'])
            event_stop = parser.isoparse(event['stop'])

            # Convertir las fechas de UTC a la zona horaria de México
            event_start_mx = event_start.astimezone(mexico_tz)
            event_stop_mx = event_stop.astimezone(mexico_tz)

            # Actualizar las fechas en formato ISO en la zona horaria de México
            event.update({
                'start': event_start_mx.strftime('%Y-%m-%dT%H:%M:%S'),
                'stop': event_stop_mx.strftime('%Y-%m-%dT%H:%M:%S')
            })

        # Devolver los eventos con las fechas convertidas
        return jsonify({'status': 'success', 'events': events}), 200

    except Exception as e:
        # En caso de error, devolver el mensaje de error
        return jsonify({'status': 'error', 'message': str(e)}), 500
