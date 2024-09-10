from flask import Blueprint, request, jsonify
from services.odoo_service import create_opportunity_in_odoo
import sys

opportunity_blueprint = Blueprint('opportunity', __name__)

@opportunity_blueprint.route('/create_opportunity', methods=['POST'])
def create_opportunity():
    try:
        data = request.json
        print(f"Datos recibidos para crear oportunidad: {data}")
        sys.stdout.flush()

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
