from flask import jsonify, request
from datetime import datetime, timedelta
import requests
import pytz

def available_slots(models, db, uid, password, mexico_tz):
    try:
        start_time, end_time, company_id = (request.args.get(k) for k in ['start_time', 'end_time', 'company_id'])
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        event_api_url = f'https://crm.gestpro.cloud/events?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        response = requests.get(event_api_url)
        if response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {response.text}")

        busy_times = [(mexico_tz.localize(datetime.strptime(e['start'], '%Y-%m-%d %H:%M:%S')),
                       mexico_tz.localize(datetime.strptime(e['stop'], '%Y-%m-%d %H:%M:%S')))
                      for e in response.json()['events']]

        working_hours = [(f"{h:02}:00", f"{h+1:02}:00") for h in range(24)]
        available_slots = []
        current_time, end_dt = (mexico_tz.localize(datetime.strptime(t, '%Y-%m-%dT%H:%M:%S')) for t in [start_time, end_time])

        while current_time + timedelta(hours=1) <= end_dt:
            next_time = current_time + timedelta(hours=1)
            time_slot = (current_time.strftime('%H:%M'), next_time.strftime('%H:%M'))

            if time_slot in working_hours and all(next_time <= b[0] or current_time >= b[1] for b in busy_times) and current_time > datetime.now(mexico_tz):
                available_slots.append({'start': current_time.strftime('%Y-%m-%d %H:%M:%S'), 'stop': next_time.strftime('%Y-%m-%d %H:%M:%S')})

            current_time = next_time

        return jsonify({'status': 'success', 'available_slots': available_slots}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
