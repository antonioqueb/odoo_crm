from flask import jsonify, request
from datetime import datetime
import pytz

def create_opportunity(models, db, uid, password, mexico_tz):
    try:
        data = request.json

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

        event_data = {
            'name': f'Consultoría para {partner_name}',
            'start': start_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'stop': end_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'partner_ids': [(6, 0, [partner_id])],
            'company_id': company_id,
        }

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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
