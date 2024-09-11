from flask import jsonify, request
from datetime import datetime, timedelta
import requests
import pytz

def available_slots(models, db, uid, password, mexico_tz):
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = request.args.get('company_id')

        if not start_time or not end_time or not company_id:
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        event_api_url = f'https://crm.gestpro.cloud/events?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        response = requests.get(event_api_url)

        if response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {response.text}")

        events_data = response.json()

        busy_times = [(event['start'], event['stop']) for event in events_data['events']]

        busy_times = [(mexico_tz.localize(datetime.strptime(start, '%Y-%m-%d %H:%M:%S')),
                       mexico_tz.localize(datetime.strptime(stop, '%Y-%m-%d %H:%M:%S')))
                      for start, stop in busy_times]

        working_hours = [
            ("00:00", "01:00"),
            ("01:00", "02:00"),
            ("02:00", "03:00"),
            ("03:00", "04:00"),
            ("04:00", "05:00"),
            ("05:00", "06:00"),
            ("06:00", "07:00"),
            ("07:00", "08:00"),
            ("08:00", "09:00"),
            ("09:00", "10:00"),
            ("10:00", "11:00"),
            ("11:00", "12:00"),
            ("12:00", "13:00"),
            ("13:00", "14:00"),
            ("14:00", "15:00"),
            ("15:00", "16:00"),
            ("16:00", "17:00"),
            ("17:00", "18:00"),
            ("18:00", "19:00"),
            ("19:00", "20:00"),
            ("20:00", "21:00"),
            ("21:00", "22:00"),
            ("22:00", "23:00"),
            ("23:00", "00:00")
        ]

        available_slots = []
        current_time = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
        end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

        while current_time + timedelta(hours=1) <= end_dt:
            next_time = current_time + timedelta(hours=1)
            current_time_str = current_time.strftime('%H:%M')
            next_time_str = next_time.strftime('%H:%M')

            if (current_time_str, next_time_str) in working_hours:
                is_free = True

                for busy_start, busy_end in busy_times:
                    if not (next_time <= busy_start or current_time >= busy_end):
                        is_free = False
                        break

                if is_free and current_time > datetime.now(mexico_tz):
                    available_slots.append({
                        'start': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'stop': next_time.strftime('%Y-%m-%d %H:%M:%S')
                    })

            current_time = next_time

        return jsonify({
            'status': 'success',
            'available_slots': available_slots
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
