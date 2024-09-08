from flask import Flask, request, jsonify
import xmlrpc.client
import os
from datetime import datetime

app = Flask(__name__)

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

        # Si no existe partner_id, crear el partner
        if not partner_id and partner_name and partner_email:
            partner_id = models.execute_kw(
                db, uid, password, 'res.partner', 'create', [{
                    'name': partner_name,
                    'email': partner_email,
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
        
        # Validar que no exista ya un evento en el mismo rango de horas
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_count', [[
                ('start', '<=', end_time),
                ('stop', '>=', start_time),
                ('user_id', '=', user_id),
                ('company_id', '=', company_id),  # Filtrar por empresa
            ]]
        )

        if events == 0:
            models.execute_kw(db, uid, password, 'calendar.event', 'create', [event_data])
        else:
            return jsonify({
                'status': 'error',
                'message': 'Este horario ya está reservado para otro evento.'
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


@app.route('/company_availability', methods=['GET'])
def company_availability():
    try:
        # Obtener parámetros de consulta (rango de fechas y empresa)
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = int(request.args.get('company_id'))

        # Buscar eventos en el calendario para la empresa específica en el rango de tiempo dado
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '>=', start_time),
                ('stop', '<=', end_time),
                ('company_id', '=', company_id),
            ]],
            {'fields': ['name', 'start', 'stop', 'user_id', 'partner_ids']}
        )

        return jsonify({
            'status': 'success',
            'events': events
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
