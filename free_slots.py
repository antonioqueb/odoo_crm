from flask import jsonify, request
import requests
import sys
from dateutil import parser
import pytz

# Función para formatear las fechas de los eventos y eliminar la información de la zona horaria
def format_events(events):
    formatted_events = []
    for event in events:
        # Parseamos las fechas recibidas
        event_start = parser.isoparse(event['start'])
        event_stop = parser.isoparse(event['stop'])
        
        # Convertimos las fechas a formato sin zona horaria (ignoramos la parte -06:00)
        formatted_event = {
            'id': event['id'],
            'start': event_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'stop': event_stop.strftime('%Y-%m-%dT%H:%M:%S')
        }
        formatted_events.append(formatted_event)
    
    return formatted_events

def free_slots(models, db, uid, password):
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

        # **Primero**: Obtener los slots disponibles
        slot_api_url = (
            f'https://crm.gestpro.cloud/available_slots?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        )
        slot_response = requests.get(slot_api_url)
        if slot_response.status_code != 200:
            raise Exception(f"Error al consultar la API de slots: {slot_response.text}")
        
        slots = slot_response.json().get('available_slots', [])
        print(f"Slots disponibles recibidos: {slots}")
        sys.stdout.flush()

        # **Segundo**: Obtener los eventos ocupados
        event_api_url = (
            f'https://crm.gestpro.cloud/events?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        )
        event_response = requests.get(event_api_url)
        if event_response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {event_response.text}")
        
        events = event_response.json().get('events', [])
        print(f"Eventos recibidos: {events}")
        sys.stdout.flush()

        # Formatear los eventos para eliminar la información de zona horaria y dejarlos en el formato deseado
        events = format_events(events)

        # **Tercero**: Comparar los slots con los eventos para eliminar solapamientos
        free_slots = []

        # Función para verificar solapamiento entre dos rangos de tiempo
        def is_overlap(slot_start, slot_stop, event_start, event_stop):
            return max(slot_start, event_start) < min(slot_stop, event_stop)

        # Convertimos las fechas de slots y eventos en objetos datetime para una comparación precisa
        for slot in slots:
            slot_start = parser.isoparse(slot['start'])
            slot_stop = parser.isoparse(slot['stop'])

            # Asegurarse de que las fechas tienen zona horaria (UTC por defecto si no tienen)
            if slot_start.tzinfo is None:
                slot_start = slot_start.replace(tzinfo=pytz.UTC)
            if slot_stop.tzinfo is None:
                slot_stop = slot_stop.replace(tzinfo=pytz.UTC)

            # Verificar si el slot se solapa con algún evento
            overlap = False
            for event in events:
                event_start = parser.isoparse(event['start'])
                event_stop = parser.isoparse(event['stop'])

                # Asegurarse de que las fechas de eventos tienen zona horaria (UTC por defecto si no tienen)
                if event_start.tzinfo is None:
                    event_start = event_start.replace(tzinfo=pytz.UTC)
                if event_stop.tzinfo is None:
                    event_stop = event_stop.replace(tzinfo=pytz.UTC)

                # Comparar rangos de tiempo (solapamiento)
                if is_overlap(slot_start, slot_stop, event_start, event_stop):
                    overlap = True
                    print(f"Solapamiento detectado: Slot {slot['start']} - {slot['stop']} con Evento {event['start']} - {event['stop']}")
                    sys.stdout.flush()
                    break

            # Si no hay solapamiento, agregar el slot a la lista de free_slots
            if not overlap:
                free_slots.append(slot)

            # Imprimir detalles de los slots comparados
            print(f"Slot: {slot['start']} - {slot['stop']} | ¿Solapado?: {'Sí' if overlap else 'No'}")
            sys.stdout.flush()

        # Logs de los slots libres
        print(f"Slots libres encontrados: {free_slots}")
        sys.stdout.flush()

        return jsonify({'status': 'success', 'free_slots': free_slots}), 200

    except Exception as e:
        print(f"Error en la función free_slots: {str(e)}")
        sys.stdout.flush()
        return jsonify({'status': 'error', 'message': str(e)}), 500
