# free_slots.py
from flask import jsonify, request
from datetime import datetime
import requests
import pytz

def free_slots(models, db, uid, password, mexico_tz):
    try:
        # Obtener parámetros de la solicitud
        start_time, end_time, company_id = (
            request.args.get(k) for k in ['start_time', 'end_time', 'company_id']
        )
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        # Consultar eventos programados
        event_api_url = (
            f'https://crm.gestpro.cloud/events?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        )
        event_response = requests.get(event_api_url)
        if event_response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {event_response.text}")
        events = event_response.json()['events']

        # Consultar slots disponibles
        slot_api_url = (
            f'https://crm.gestpro.cloud/available_slots?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        )
        slot_response = requests.get(slot_api_url)
        if slot_response.status_code != 200:
            raise Exception(f"Error al consultar la API de slots: {slot_response.text}")
        slots = slot_response.json()['available_slots']

        # Convertir eventos a objetos datetime en UTC
        busy_times = [
            (
                pytz.utc.localize(datetime.strptime(e['start'], '%Y-%m-%dT%H:%M:%SZ')).astimezone(mexico_tz),
                pytz.utc.localize(datetime.strptime(e['stop'], '%Y-%m-%dT%H:%M:%SZ')).astimezone(mexico_tz)
            )
            for e in events
        ]

        # Restar eventos de slots para obtener slots libres
        free_slots = []
        for slot in slots:
            slot_start = mexico_tz.localize(datetime.strptime(slot['start'], '%Y-%m-%dT%H:%M:%SZ')).astimezone(pytz.utc)
            slot_stop = mexico_tz.localize(datetime.strptime(slot['stop'], '%Y-%m-%dT%H:%M:%SZ')).astimezone(pytz.utc)
            
            # Verificar solapamiento con eventos ocupados
            if all(slot_stop <= event_start or slot_start >= event_stop for event_start, event_stop in busy_times):
                free_slots.append({
                    'start': slot_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'stop': slot_stop.strftime('%Y-%m-%dT%H:%M:%SZ')
                })

        return jsonify({'status': 'success', 'free_slots': free_slots}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
