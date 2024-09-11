from flask import Blueprint, request, jsonify
from app.services.odoo_service import create_opportunity_in_odoo
from app.utils.time_utils import local_to_utc
import sys

opportunity_blueprint = Blueprint('opportunity', __name__)

@opportunity_blueprint.route('/create_opportunity', methods=['POST'])
def create_opportunity():
    try:
        data = request.json
        print(f"Datos recibidos para crear oportunidad: {data}")
        sys.stdout.flush()

        # Convertir las horas locales a UTC antes de pasar a Odoo
        if 'start_time' in data:
            data['start_time'] = local_to_utc(data['start_time'])
        if 'end_time' in data:
            data['end_time'] = local_to_utc(data['end_time'])

        # Llamar al servicio que crea la oportunidad en Odoo
        opportunity_id = create_opportunity_in_odoo(data)

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
