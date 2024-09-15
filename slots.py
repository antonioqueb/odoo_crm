# slots.py
from flask import jsonify, request
from datetime import datetime, timedelta
import requests
import pytz
from dateutil import parser

def available_slots(models, db, uid, password, mexico_tz):
    try:
        # Obtener parámetros de la solicitud
        start_time, end_time, company_id = (
            request.args.get(k) for k in ['start_time', 'end_time', 'company_id']
        )
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        # Consultar eventos programados desde la API de eventos
        event_api_url = (
            f'https://crm.gestpro.cloud/events?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        )
        response = requests.get(event_api_url)
        if response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {response.text}")

        # Convertir eventos a objetos datetime en UTC y luego a la zona horaria de México
        busy_times = []
        for e in response.json()['events']:
            event_start = parser.isoparse(e['start'])
            event_stop = parser.isoparse(e['stop'])

            # Asegurarse de que las fechas están en UTC
            if event_start.tzinfo is None:
                event_start = mexico_tz.localize(event_start).astimezone(pytz.utc)
            else:
                event_start = event_start.astimezone(pytz.utc)
            
            if event_stop.tzinfo is None:
                event_stop = mexico_tz.localize(event_stop).astimezone(pytz.utc)
            else:
                event_stop = event_stop.astimezone(pytz.utc)

            busy_times.append((event_start, event_stop))

        # Definir horas de trabajo (por ejemplo, 00:00 a 23:00)
        working_hours = [(f"{h:02}:00", f"{h+1:02}:00") for h in range(24)]
        available_slots = []

        # Parsear tiempos de inicio y fin como UTC y convertir a la zona horaria de México
        current_time = parser.isoparse(start_time)
        end_dt = parser.isoparse(end_time)

        # Asegurarse de que las fechas están en UTC
        if current_time.tzinfo is None:
            current_time = pytz.utc.localize(current_time).astimezone(mexico_tz)
        else:
            current_time = current_time.astimezone(mexico_tz)
        
        if end_dt.tzinfo is None:
            end_dt = pytz.utc.localize(end_dt).astimezone(mexico_tz)
        else:
            end_dt = end_dt.astimezone(mexico_tz)

        while current_time + timedelta(hours=1) <= end_dt:
            next_time = current_time + timedelta(hours=1)
            time_slot = (current_time.strftime('%H:%M'), next_time.strftime('%H:%M'))

            # Verificar si el slot está dentro de las horas de trabajo y no está ocupado
            if (
                time_slot in working_hours and 
                all(next_time <= b[0] or current_time >= b[1] for b in busy_times) and 
                current_time > datetime.now(mexico_tz)
            ):
                # Convertir a UTC con sufijo 'Z' para mantener consistencia
                slot_start_utc = current_time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                slot_stop_utc = next_time.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                available_slots.append({'start': slot_start_utc, 'stop': slot_stop_utc})

            current_time = next_time

        return jsonify({'status': 'success', 'available_slots': available_slots}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
