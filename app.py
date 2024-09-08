from flask import Flask, request, jsonify
import xmlrpc.client
import os
from datetime import datetime, timedelta

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
                'company_id': company_id,
            }]
        )

        # Verificar disponibilidad en el calendario y crear un evento
        start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(hours=1)
        
        # Verificar que el bloque de tiempo esté libre
        calendar_events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ['start', '<=', end_date.isoformat()],
                ['stop', '>=', start_date.isoformat()]
            ]],
            {'fields': ['start', 'stop']}
        )

        if calendar_events:
            return jsonify({
                'status': 'error',
                'message': 'El bloque de tiempo ya está ocupado.'
            }), 409

        # Crear el evento en el calendario
        event_id = models.execute_kw(
            db, uid, password, 'calendar.event', 'create', [{
                'name': f'Consulta con {partner_name}',
                'start': start_date.isoformat(),
                'stop': end_date.isoformat(),
                'partner_ids': [(4, partner_id)],  # Relacionar con el cliente
                'allday': False,
                'user_id': user_id,
                'company_id': company_id,
            }]
        )

        return jsonify({
            'status': 'success',
            'opportunity_id': opportunity_id,
            'calendar_event_id': event_id
        }), 201

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
