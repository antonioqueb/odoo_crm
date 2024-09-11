from flask import jsonify, request
from datetime import datetime
import pytz

def get_events(models, db, uid, password, mexico_tz):
    try:
        # Obtener los parámetros de la solicitud
        start_time, end_time, company_id = (request.args.get(k) for k in ['start_time', 'end_time', 'company_id'])
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")
        
        # Convertir los tiempos a la zona horaria de México
        start_dt = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
        end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

        # Consultar los eventos en la base de datos de Odoo
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_time), ('stop', '>=', start_time), ('company_id', '=', int(company_id))
            ]], {'fields': ['start', 'stop']}
        )

        # Formatear cada evento
        formatted_events = []
        for event in events:
            # Convertir las fechas a la zona horaria de México y al formato adecuado
            event_start_mx = pytz.utc.localize(datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')).astimezone(mexico_tz)
            event_stop_mx = pytz.utc.localize(datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')).astimezone(mexico_tz)
            
            # Actualizar los valores en el formato correcto y agregarlos a la lista de eventos formateados
            formatted_events.append({
                'start': event_start_mx.strftime('%Y-%m-%d %H:%M:%S'),
                'stop': event_stop_mx.strftime('%Y-%m-%d %H:%M:%S')
            })

        # Retornar la respuesta en formato JSON
        return jsonify(formatted_events), 200

    except Exception as e:
        # Manejo de errores
        return jsonify({'status': 'error', 'message': str(e)}), 500
