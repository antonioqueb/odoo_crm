from flask import jsonify, request
import requests
import sys
from dateutil import parser

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

        # **Tercero**: Comparar los slots con los eventos para eliminar solapamientos
        free_slots = []
        
        # Función para verificar solapamiento entre dos rangos de tiempo
        def is_overlap(slot_start, slot_stop, event_start, event_stop):
            return max(slot_start, event_start) < min(slot_stop, event_stop)

        # Convertimos las fechas de slots y eventos en objetos datetime para una comparación precisa
        for slot in slots:
            slot_start = parser.isoparse(slot['start'])
            slot_stop = parser.isoparse(slot['stop'])

            # Verificar si el slot se solapa con algún evento
            overlap = False
            for event in events:
                event_start = parser.isoparse(event['start'])
                event_stop = parser.isoparse(event['stop'])

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
