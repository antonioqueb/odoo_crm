from flask import jsonify, request
import requests
import sys

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

        # **Tercero**: Comparar las fechas como texto plano
        free_slots = []
        event_times = [(event['start'], event['stop']) for event in events]

        for slot in slots:
            slot_times = (slot['start'], slot['stop'])

            # Comparar si el slot está en el conjunto de eventos
            if slot_times not in event_times:
                free_slots.append(slot)

            # Imprimir detalles de los slots comparados
            print(f"Slot: {slot['start']} - {slot['stop']} | ¿Coincide con evento?: {'Sí' if slot_times in event_times else 'No'}")
            sys.stdout.flush()

        # Logs de los slots libres
        print(f"Slots libres encontrados: {free_slots}")
        sys.stdout.flush()

        return jsonify({'status': 'success', 'free_slots': free_slots}), 200

    except Exception as e:
        print(f"Error en la función free_slots: {str(e)}")
        sys.stdout.flush()
        return jsonify({'status': 'error', 'message': str(e)}), 500
