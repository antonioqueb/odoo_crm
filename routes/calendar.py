from flask import Blueprint, request, jsonify
from services.odoo_service import get_available_slots, get_events
import sys

calendar_blueprint = Blueprint('calendar', __name__)

@calendar_blueprint.route('/available_slots', methods=['GET'])
def available_slots():
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        company_id = request.args.get('company_id')

        available_slots = get_available_slots(start_time, end_time, company_id)

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

        events = get_events(start_time, end_time, company_id)

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
