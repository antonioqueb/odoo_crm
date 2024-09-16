from flask import jsonify, request
from datetime import datetime, timedelta
import requests
import pytz
from dateutil import parser
import sys  # ** Importación de sys **

def free_slots(models, db, uid, password, mexico_tz):
    try:
        # Obtener parámetros de la solicitud
        start_time, end_time, company_id = (
            request.args.get(k) for k in ['start_time', 'end_time', 'company_id']
        )
        if not all([start_time, end_time, company_id]):
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        # Logs de los parámetros recibidos
        print(f"Parámetros recibidos: start_time={start_time}, end_time={end_time}, company_id={company_id}")
        sys.stdout.flush()

        # Obtener los eventos programados
        event_api_url = (
            f'https://crm.gestpro.cloud/events?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        )
        event_response = requests.get(event_api_url)
        if event_response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {event_response.text}")
        
        events = event_response.json()['events']
        print(f"Eventos recibidos: {events}")
        sys.stdout.flush()

        # Obtener los slots disponibles
        slot_api_url = (
            f'https://crm.gestpro.cloud/available_slots?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        )
        slot_response = requests.get(slot_api_url)
        if slot_response.status_code != 200:
            raise Exception(f"Error al consultar la API de slots: {slot_response.text}")
        
        slots = slot_response.json()['available_slots']
        print(f"Slots disponibles recibidos: {slots}")
        sys.stdout.flush()

        # Convertir los eventos en un formato manejable
        busy_times = []
        for e in events:
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
        
        # Logs de los tiempos ocupados
        print(f"Tiempos ocupados: {busy_times}")
        sys.stdout.flush()

        # Convertir los slots a objetos datetime y restarlos de los tiempos ocupados
        free_slots = []
        for slot in slots:
            slot_start = parser.isoparse(slot['start'])
            slot_stop = parser.isoparse(slot['stop'])

            # Asegurarse de que las fechas están en UTC
            if slot_start.tzinfo is None:
                slot_start = mexico_tz.localize(slot_start).astimezone(pytz.utc)
            else:
                slot_start = slot_start.astimezone(pytz.utc)
            
            if slot_stop.tzinfo is None:
                slot_stop = mexico_tz.localize(slot_stop).astimezone(pytz.utc)
            else:
                slot_stop = slot_stop.astimezone(pytz.utc)

            # **Restricción del tiempo de fin:**
            # Asegurar que los slots no excedan las 23:00 del mismo día
            day_end = parser.isoparse(end_time).replace(hour=23, minute=0, second=0, microsecond=0)
            if slot_stop > day_end:
                slot_stop = day_end  # Limitar el tiempo de fin a las 23:00

            # Verificar solapamiento con eventos ocupados
            overlap = False
            for event_start, event_stop in busy_times:
                if not (slot_stop <= event_start or slot_start >= event_stop):
                    overlap = True
                    break
            if not overlap:
                free_slots.append({
                    'start': slot_start.strftime('%Y-%m-%dT%H:%M:%S'),  # Quitar la 'Z'
                    'stop': slot_stop.strftime('%Y-%m-%dT%H:%M:%S')  # Quitar la 'Z'
                })

        # Logs de los slots libres
        print(f"Slots libres encontrados: {free_slots}")
        sys.stdout.flush()

        return jsonify({'status': 'success', 'free_slots': free_slots}), 200

    except Exception as e:
        print(f"Error en la función free_slots: {str(e)}")
        sys.stdout.flush()
        return jsonify({'status': 'error', 'message': str(e)}), 500
