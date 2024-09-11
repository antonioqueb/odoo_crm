from flask import jsonify, request
from datetime import datetime
import pytz
import logging

def get_events(models, db, uid, password, mexico_tz):
    try:
        start_time, end_time, company_id = (request.args.get(k) for k in ['start_time', 'end_time', 'company_id'])
        
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")
        
        start_dt = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
        end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

        # Consulta en la base de datos de eventos
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_time), ('stop', '>=', start_time), ('company_id', '=', int(company_id))
            ]], {'fields': ['id', 'name', 'start', 'stop', 'company_id', 'user_id', 'partner_ids', 'description', 'allday', 'location']}
        )

        if not isinstance(events, list):
            raise ValueError("La respuesta de 'search_read' no es una lista.")
        
        # Formateo de eventos
        formatted_events = []
        for event in events:
            if isinstance(event, dict):
                event_start_mx = pytz.utc.localize(datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')).astimezone(mexico_tz)
                event_stop_mx = pytz.utc.localize(datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')).astimezone(mexico_tz)
                
                formatted_events.append({
                    "start": event_start_mx.strftime('%Y-%m-%d %H:%M:%S'),
                    "stop": event_stop_mx.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                logging.error(f"El evento no es un diccionario: {event}")
        
        return jsonify(formatted_events), 200

    except Exception as e:
        logging.error(f"Error al obtener eventos: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
