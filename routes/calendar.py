from flask import Blueprint, request, jsonify
from services.odoo_service import get_available_slots, get_events
from utils.time_utils import local_to_utc
import sys

calendar_blueprint = Blueprint('calendar', __name__)

@calendar_blueprint.route('/available_slots', methods=['GET'])
def available_slots():
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = request.args.get('company_id')

        # Convertir las horas locales a UTC solo si son cadenas
        start_time_utc = local_to_utc(start_time) if isinstance(start_time, str) else start_time
        end_time_utc = local_to_utc(end_time) if isinstance(end_time, str) else end_time

        available_slots = get_available_slots(start_time_utc, end_time_utc, company_id)

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

@calendar_blueprint.route('/events', methods=['GET'])
def events():
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = request.args.get('company_id')

        # Convertir las horas locales a UTC antes de pasar a Odoo
        start_time_utc = local_to_utc(start_time)
        end_time_utc = local_to_utc(end_time)

        events = get_events(start_time_utc, end_time_utc, company_id)

        return jsonify({
            'status': 'success',
            'events': events
        }), 200

    except Exception as e:
        print(f"Error en events: {str(e)}")
        sys.stdout.flush()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
