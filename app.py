from flask import Flask, request, jsonify
import xmlrpc.client
import os
from datetime import datetime, timedelta
import pytz
from flask_cors import CORS
import sys
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://inventario-plus.gestpro.cloud"}})

odoo_url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USERNAME')
password = os.getenv('ODOO_PASSWORD')

common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

mexico_tz = pytz.timezone('America/Mexico_City')

@app.route('/create_opportunity', methods=['POST'])
def create_opportunity():
    try:
        data = request.json
        print(f"Datos recibidos para crear oportunidad: {data}")
        sys.stdout.flush()

        name = data.get('name')
        partner_id = data.get('partner_id')
        partner_name = data.get('partner_name')
        partner_email = data.get('partner_email')
        user_id = data.get('user_id')
        stage_id = data.get('stage_id')
        expected_revenue = data.get('expected_revenue')
        probability = data.get('probability')
        company_id = data.get('company_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        phone = data.get('phone')

        if not partner_id and partner_name and partner_email:
            print(f"Creando partner en Odoo con los siguientes datos: name={partner_name}, email={partner_email}, phone={phone}")
            sys.stdout.flush()
            partner_id = models.execute_kw(
                db, uid, password, 'res.partner', 'create', [{
                    'name': partner_name,
                    'email': partner_email,
                    'phone': phone,  
                }]
            )

        start_time_local = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
        end_time_local = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'))
        start_time_utc = start_time_local.astimezone(pytz.utc)
        end_time_utc = end_time_local.astimezone(pytz.utc)

        print(f"Creando oportunidad en Odoo con los siguientes datos: name={name}, partner_id={partner_id}, user_id={user_id}, stage_id={stage_id}, expected_revenue={expected_revenue}, probability={probability}, company_id={company_id}, phone={phone}")
        sys.stdout.flush()
        opportunity_id = models.execute_kw(
            db, uid, password, 'crm.lead', 'create', [{
                'name': name,
                'partner_id': partner_id,
                'user_id': user_id,
                'stage_id': stage_id,
                'expected_revenue': expected_revenue,
                'probability': probability,
                'company_id': company_id,
                'phone': phone,
            }]
        )
        print(f"Oportunidad creada en Odoo con ID: {opportunity_id}")
        sys.stdout.flush()

        event_data = {
            'name': f'Consultoría para {partner_name}',
            'start': start_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'stop': end_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'partner_ids': [(6, 0, [partner_id])],
            'company_id': company_id,
        }

        print(f"Enviando fechas a Odoo en UTC: start={start_time_utc}, stop={end_time_utc}")
        sys.stdout.flush()

        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_count', [[
                ('start', '<=', end_time_utc.strftime('%Y-%m-%d %H:%M:%S')),
                ('stop', '>=', start_time_utc.strftime('%Y-%m-%d %H:%M:%S'))
            ]]
        )

        if events == 0:
            models.execute_kw(db, uid, password, 'calendar.event', 'create', [event_data])
        else:
            return jsonify({
                'status': 'error',
                'message': 'Este horario ya está reservado para otro evento en la misma empresa.'
            }), 400

        return jsonify({
            'status': 'success',
            'opportunity_id': opportunity_id
        }), 201

    except Exception as e:
        print(f"Error en create_opportunity: {str(e)}")
        sys.stdout.flush()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/available_slots', methods=['GET'])
def available_slots():
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = request.args.get('company_id')

        if not start_time or not end_time or not company_id:
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        print(f"Fechas recibidas: start_time={start_time}, end_time={end_time}, company_id={company_id}")
        sys.stdout.flush()

        # Hacer una solicitud HTTP al endpoint de eventos para obtener los eventos ocupados
        event_api_url = f'https://crm.gestpro.cloud/events?start_time={start_time}&end_time={end_time}&company_id={company_id}'
        response = requests.get(event_api_url)

        if response.status_code != 200:
            raise Exception(f"Error al consultar la API de eventos: {response.text}")

        events_data = response.json()

        busy_times = [(event['start'], event['stop']) for event in events_data['events']]
        
        # Convertir los tiempos ocupados a objetos datetime en la zona horaria de México
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
                print(f"Comprobando bloque: {current_time} - {next_time}")

                for busy_start, busy_end in busy_times:
                    print(f"Comparando con evento: {busy_start} - {busy_end}")
                    if not (next_time <= busy_start or current_time >= busy_end):
                        is_free = False
                        print(f"Solapamiento detectado con el evento: {busy_start} - {busy_end}")
                        break

                if is_free and current_time > datetime.now(mexico_tz):
                    print(f"Bloque disponible: {current_time} - {next_time}")
                    available_slots.append({
                        'start': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'end': next_time.strftime('%Y-%m-%d %H:%M:%S')
                    })

            current_time = next_time

        return jsonify({
            'status': 'success',
            'available_slots': available_slots
        }), 200

    except Exception as e:
        print(f"Error en available_slots: {str(e)}")
        sys.stdout.flush()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/events', methods=['GET'])
def get_events():
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = request.args.get('company_id')

        if not start_time or not end_time or not company_id:
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        start_dt = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
        end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

        print(f"Consultando eventos de Odoo con: start_time <= {end_time}, stop >= {start_time}, company_id={company_id}")
        sys.stdout.flush()

        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_time),
                ('stop', '>=', start_time),
                ('company_id', '=', int(company_id))
            ]],
            {'fields': ['id', 'name', 'start', 'stop', 'company_id', 'user_id', 'partner_ids', 'description', 'allday', 'location']}
        )

        print(f"Eventos obtenidos de Odoo: {events}")
        sys.stdout.flush()

        for event in events:
            event_start_utc = datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')
            event_stop_utc = datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')

            event_start_mx = pytz.utc.localize(event_start_utc).astimezone(mexico_tz)
            event_stop_mx = pytz.utc.localize(event_stop_utc).astimezone(mexico_tz)

            event['start'] = event_start_mx.strftime('%Y-%m-%d %H:%M:%S')
            event['stop'] = event_stop_mx.strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'status': 'success',
            'events': events
        }), 200

    except Exception as e:
        print(f"Error al obtener eventos: {str(e)}")
        sys.stdout.flush()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
