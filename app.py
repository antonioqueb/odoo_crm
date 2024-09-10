from flask import Flask, request, jsonify
import xmlrpc.client
import os
from datetime import datetime, timedelta
import pytz  # Biblioteca para manejo de zonas horarias
from flask_cors import CORS
import sys  # Para asegurar que los prints se descarguen de inmediato
from event_service import fetch_events  # Importar la función separada

app = Flask(__name__)

# Habilitar CORS para permitir solicitudes solo desde el dominio especificado
CORS(app, resources={r"/*": {"origins": "https://inventario-plus.gestpro.cloud"}})

# Leer las variables de entorno
odoo_url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USERNAME')
password = os.getenv('ODOO_PASSWORD')

# Inicializar conexión a Odoo
common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

# Zona horaria de la Ciudad de México
mexico_tz = pytz.timezone('America/Mexico_City')

@app.route('/create_opportunity', methods=['POST'])
def create_opportunity():
    try:
        # Extraer datos del cuerpo de la solicitud
        data = request.json
        print(f"Datos recibidos para crear oportunidad: {data}")
        sys.stdout.flush()

        # Parámetros para crear una oportunidad
        name = data.get('name')
        partner_id = data.get('partner_id')
        partner_name = data.get('partner_name')
        partner_email = data.get('partner_email')
        user_id = data.get('user_id')  # Representante asignado (opcional)
        stage_id = data.get('stage_id')  # Etapa de la oportunidad (opcional)
        expected_revenue = data.get('expected_revenue')  # Ingresos esperados
        probability = data.get('probability')  # Probabilidad de éxito
        company_id = data.get('company_id')  # ID de la empresa (multiempresa)
        start_time = data.get('start_time')  # Hora de inicio para el evento en el calendario
        end_time = data.get('end_time')  # Hora de fin para el evento en el calendario
        phone = data.get('phone')  # Agregamos el teléfono

        # Si no existe partner_id, crear el partner
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

        # Convertir las fechas a UTC antes de enviarlas a Odoo
        start_time_local = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
        end_time_local = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'))
        start_time_utc = start_time_local.astimezone(pytz.utc)
        end_time_utc = end_time_local.astimezone(pytz.utc)

        # Crear la oportunidad en el modelo 'crm.lead'
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
                'company_id': company_id,  # Asignación de la empresa
                'phone': phone,
            }]
        )
        print(f"Oportunidad creada en Odoo con ID: {opportunity_id}")
        sys.stdout.flush()

        # Crear un evento en el calendario para el rango de horas especificado
        event_data = {
            'name': f'Consultoría para {partner_name}',
            'start': start_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'stop': end_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'partner_ids': [(6, 0, [partner_id])],
            'company_id': company_id,  # Asignación de la empresa al evento
        }

        # Imprimir las fechas en UTC antes de enviarlas a Odoo
        print(f"Enviando fechas a Odoo en UTC: start={start_time_utc}, stop={end_time_utc}")
        sys.stdout.flush()

        # Validar que no exista ya un evento en el mismo rango de horas para la misma empresa
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_count', [[
                ('start', '<=', end_time_utc.strftime('%Y-%m-%d %H:%M:%S')),
                ('stop', '>=', start_time_utc.strftime('%Y-%m-%d %H:%M:%S')),
                ('user_id', '=', user_id),
                ('company_id', '=', company_id),  # Filtrar por la misma empresa
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
        # Obtener parámetros de consulta (rango de fechas y empresa)
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = request.args.get('company_id')

        # Verificar que todos los parámetros necesarios estén presentes
        if not start_time or not end_time or not company_id:
            raise ValueError("Los parámetros start_time, end_time y company_id son obligatorios.")

        # Imprimir las fechas recibidas
        print(f"Fechas recibidas: start_time={start_time}, end_time={end_time}")
        sys.stdout.flush()

        # Convertir company_id a entero
        company_id = int(company_id)

        # Obtener los eventos y los tiempos ocupados usando la función separada
        busy_times, events = fetch_events(models, db, uid, password, start_time, end_time, company_id, mexico_tz)

        # Horarios disponibles que te interesan (horas fijas que quieres aceptar)
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

        # Definir bloques de tiempo disponibles de una hora
        available_slots = []
        current_time = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
        end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

        while current_time + timedelta(hours=1) <= end_dt:
            next_time = current_time + timedelta(hours=1)

            # Convertir horas a string para comparación
            current_time_str = current_time.strftime('%H:%M')
            next_time_str = next_time.strftime('%H:%M')

            # Verificar si el bloque de tiempo coincide con los horarios de trabajo
            if (current_time_str, next_time_str) in working_hours:
                is_free = True
                print(f"Comprobando bloque: {current_time} - {next_time}")
                for busy_start, busy_end in busy_times:
                    # Verificar si hay solapamiento entre el bloque de tiempo actual y algún evento ocupado
                    print(f"Comparando con evento: {busy_start} - {busy_end}")
                    if busy_start < next_time and busy_end > current_time:
                        is_free = False
                        print(f"Solapamiento detectado con el evento: {busy_start} - {busy_end}")
                        break

                # Verificar si el bloque de tiempo está en el futuro
                if is_free and current_time > datetime.now(mexico_tz):
                    print(f"Bloque disponible: {current_time} - {next_time}")
                    available_slots.append({
                        'start': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'end': next_time.strftime('%Y-%m-%d %H:%M:%S')
                    })

            current_time = next_time

        # Devolver los bloques disponibles junto con los eventos obtenidos
        return jsonify({
            'status': 'success',
            'available_slots': available_slots,
            'events': events  # Devolver también los eventos completos para depuración o futura referencia
        }), 200

    except Exception as e:
        print(f"Error en available_slots: {str(e)}")
        sys.stdout.flush()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
