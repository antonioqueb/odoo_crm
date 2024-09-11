from flask import jsonify, request
from datetime import datetime
import requests
import pytz

# Función que obtiene los slots libres restando los eventos ocupados
def free_slots(models, db, uid, password, mexico_tz):
    try:
        start_time, end_time, company_id = (request.args.get(k) for k in ['start_time', 'end_time', 'company_id'])
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        # Obtener los eventos programados
        event_api_url = f'https://crm.gestpro.cloud/events?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        event_response = requests.get(event_api_url)
        if event_response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {event_response.text}")
        events = event_response.json()['events']

        # Obtener los slots disponibles
        slot_api_url = f'https://crm.gestpro.cloud/available_slots?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        slot_response = requests.get(slot_api_url)
        if slot_response.status_code != 200:
            raise Exception(f"Error al consultar la API de slots: {slot_response.text}")
        slots = slot_response.json()['available_slots']

        # Convierte los eventos en un formato manejable
        busy_times = [(mexico_tz.localize(datetime.strptime(e['start'], '%Y-%m-%d %H:%M:%S')),
                       mexico_tz.localize(datetime.strptime(e['stop'], '%Y-%m-%d %H:%M:%S')))
                      for e in events]

        # Restar los eventos de los slots
        free_slots = []
        for slot in slots:
            slot_start = mexico_tz.localize(datetime.strptime(slot['start'], '%Y-%m-%d %H:%M:%S'))
            slot_stop = mexico_tz.localize(datetime.strptime(slot['stop'], '%Y-%m-%d %H:%M:%S'))
            
            # Comprobar si el slot no se solapa con ningún evento
            if all(slot_stop <= event_start or slot_start >= event_stop for event_start, event_stop in busy_times):
                free_slots.append(slot)

        return jsonify({'status': 'success', 'free_slots': free_slots}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
