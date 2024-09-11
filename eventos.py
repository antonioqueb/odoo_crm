# eventos.py

from flask import jsonify, request
from datetime import datetime
import pytz
import sys

def get_events(models, db, uid, password, mexico_tz):
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = request.args.get('company_id')

        if not start_time or not end_time or not company_id:
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        start_dt = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
        end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

        print(f"Consultando eventos de Odoo con: start_time <= {end_time}, stop >= {start_time}, company_id={company_id}")
        sys.stdout.flush()

        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_time),
                ('stop', '>=', start_time),
                ('company_id', '=', int(company_id))
            ]],
            {'fields': ['id', 'name', 'start', 'stop', 'company_id', 'user_id', 'partner_ids', 'description', 'allday', 'location']}
        )

        print(f"Eventos obtenidos de Odoo: {events}")
        sys.stdout.flush()

        for event in events:
            event_start_utc = datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')
            event_stop_utc = datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')

            event_start_mx = pytz.utc.localize(event_start_utc).astimezone(mexico_tz)
            event_stop_mx = pytz.utc.localize(event_stop_utc).astimezone(mexico_tz)

            event['start'] = event_start_mx.strftime('%Y-%m-%d %H:%M:%S')
            event['stop'] = event_stop_mx.strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'status': 'success',
            'events': events
        }), 200

    except Exception as e:
        print(f"Error al obtener eventos: {str(e)}")
        sys.stdout.flush()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
