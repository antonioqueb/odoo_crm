from flask import jsonify, request
from datetime import datetime
import pytz

def create_opportunity(models, db, uid, password, mexico_tz):
    try:
        data = request.json
        required_fields = ['name', 'partner_id', 'partner_name', 'partner_email', 'user_id', 'stage_id', 'expected_revenue', 'probability', 'company_id', 'start_time', 'end_time', 'phone']
        name, partner_id, partner_name, partner_email, user_id, stage_id, expected_revenue, probability, company_id, start_time, end_time, phone = (data.get(f) for f in required_fields)

        if not partner_id and partner_name and partner_email:
            partner_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{'name': partner_name, 'email': partner_email, 'phone': phone}])

        start_time_utc, end_time_utc = (mexico_tz.localize(datetime.strptime(t, '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc) for t in [start_time, end_time])

        opportunity_id = models.execute_kw(db, uid, password, 'crm.lead', 'create', [{
            'name': name, 'partner_id': partner_id, 'user_id': user_id, 'stage_id': stage_id, 'expected_revenue': expected_revenue, 'probability': probability, 'company_id': company_id, 'phone': phone
        }])

        event_data = {
            'name': f'Consultoría para {partner_name}', 'start': start_time_utc.strftime('%Y-%m-%d %H:%M:%S'), 'stop': end_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id, 'partner_ids': [(6, 0, [partner_id])], 'company_id': company_id
        }

        events = models.execute_kw(db, uid, password, 'calendar.event', 'search_count', [[
            ('start', '<=', end_time_utc.strftime('%Y-%m-%d %H:%M:%S')), ('stop', '>=', start_time_utc.strftime('%Y-%m-%d %H:%M:%S'))
        ]])

        if events == 0:
            models.execute_kw(db, uid, password, 'calendar.event', 'create', [event_data])
        else:
            return jsonify({'status': 'error', 'message': 'Este horario ya está reservado para otro evento en la misma empresa.'}), 400

        return jsonify({'status': 'success', 'opportunity_id': opportunity_id}), 201

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
