from flask import jsonify, request
from datetime import datetime, timedelta
import pytz
from dateutil import parser
import requests  # Agregar la importación de requests

def get_events(models, db, uid, password, mexico_tz):
    try:
        # Obtener parámetros de la solicitud
        start_time, end_time, company_id = (
            request.args.get(k) for k in ['start_time', 'end_time', 'company_id']
        )
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")
        
        # Ampliar el rango de búsqueda en 1 día por cada lado
        extended_start_time = parser.isoparse(start_time) - timedelta(days=1)
        extended_end_time = parser.isoparse(end_time) + timedelta(days=1)
        
        # Hacer la consulta a la API con el rango extendido
        event_api_url = (
            f'https://crm.gestpro.cloud/events?start_time={extended_start_time.isoformat()}&end_time={extended_end_time.isoformat()}&company_id={company_id}'
        )
        event_response = requests.get(event_api_url)
        if event_response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {event_response.text}")
        
        # Recibir los eventos de la API
        events = event_response.json().get('events', [])
        print(f"Eventos recibidos con rango extendido: {events}")
        
        # Filtrar los eventos para que solo caigan dentro del rango solicitado
        filtered_events = []
        for event in events:
            event_start = parser.isoparse(event['start'])
            event_stop = parser.isoparse(event['stop'])
            if event_start >= parser.isoparse(start_time) and event_stop <= parser.isoparse(end_time):
                filtered_events.append(event)
        
        print(f"Eventos filtrados: {filtered_events}")

        # Procesar los eventos y devolver la respuesta
        return jsonify({'status': 'success', 'events': filtered_events}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
