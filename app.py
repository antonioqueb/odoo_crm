from flask import Flask, request, jsonify
import xmlrpc.client
import os
from datetime import datetime, timedelta
from flask_cors import CORS

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

@app.route('/create_opportunity', methods=['POST'])
def create_opportunity():
    try:
        # Extraer datos del cuerpo de la solicitud
        data = request.json

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
            partner_id = models.execute_kw(
                db, uid, password, 'res.partner', 'create', [{
                    'name': partner_name,
                    'email': partner_email,
                    'phone': phone,  
                }]
            )

        # Crear la oportunidad en el modelo 'crm.lead'
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

        # Crear un evento en el calendario para el rango de horas especificado
        event_data = {
            'name': f'Consultoría para {partner_name}',
            'start': start_time,
            'stop': end_time,
            'user_id': user_id,
            'partner_ids': [(6, 0, [partner_id])],
            'company_id': company_id,  # Asignación de la empresa al evento
        }
        
        # Validar que no exista ya un evento en el mismo rango de horas para la misma empresa
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_count', [[
                ('start', '<=', end_time),
                ('stop', '>=', start_time),
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Nueva ruta para visualizar bloques de tiempo disponibles
@app.route('/available_slots', methods=['GET'])
def available_slots():
    try:
        # Obtener parámetros de consulta (rango de fechas y empresa)
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = int(request.args.get('company_id'))
        user_id = int(request.args.get('user_id'))

        # Convertir las fechas de string a objetos datetime
        start_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
        end_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')

        # Buscar eventos en el calendario para la empresa específica en el rango de tiempo dado
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '>=', start_time),
                ('stop', '<=', end_time),
                ('company_id', '=', company_id),
                ('user_id', '=', user_id),
            ]],
            {'fields': ['start', 'stop']}
        )

        # Convertir los tiempos de eventos a datetime y ordenarlos por inicio
        busy_times = [(datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S'), 
                       datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')) 
                      for event in events]
        busy_times.sort()

        # Definir bloques de tiempo disponibles de una hora
        available_slots = []
        current_time = start_dt

        while current_time + timedelta(hours=1) <= end_dt:
            next_time = current_time + timedelta(hours=1)

            # Verificar si el bloque actual está ocupado por algún evento
            is_free = True
            for busy_start, busy_end in busy_times:
                if busy_start < next_time and busy_end > current_time:
                    is_free = False
                    break

            if is_free:
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
