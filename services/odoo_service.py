from config import models, db, uid, password
from utils.time_utils import local_to_utc
import pytz
from datetime import datetime

mexico_tz = pytz.timezone('America/Mexico_City')

def create_opportunity_in_odoo(data):
    name = data.get('name')
    partner_id = data.get('partner_id')
    partner_name = data.get('partner_name')
    partner_email = data.get('partner_email')
    user_id = data.get('user_id')
    stage_id = data.get('stage_id')
    expected_revenue = data.get('expected_revenue')
    probability = data.get('probability')
    company_id = data.get('company_id')
    phone = data.get('phone')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not partner_id and partner_name and partner_email:
        partner_id = models.execute_kw(
            db, uid, password, 'res.partner', 'create', [{
                'name': partner_name,
                'email': partner_email,
                'phone': phone,
            }]
        )

    start_time_utc = local_to_utc(start_time)
    end_time_utc = local_to_utc(end_time)

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

    events = models.execute_kw(
        db, uid, password, 'calendar.event', 'search_count', [[
            ('start', '<=', end_time_utc.strftime('%Y-%m-%d %H:%M:%S')),
            ('stop', '>=', start_time_utc.strftime('%Y-%m-%d %H:%M:%S'))
        ]]
    )

    if events == 0:
        models.execute_kw(db, uid, password, 'calendar.event', 'create', [{
            'name': f'Consultoría para {partner_name}',
            'start': start_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'stop': end_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'partner_ids': [(6, 0, [partner_id])],
            'company_id': company_id,
        }])

    return opportunity_id

def get_available_slots(start_time, end_time, company_id):
    start_dt = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
    end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

    events = models.execute_kw(
        db, uid, password, 'calendar.event', 'search_read', [[
            ('start', '<=', end_dt.strftime('%Y-%m-%d %H:%M:%S')),
            ('stop', '>=', start_dt.strftime('%Y-%m-%d %H:%M:%S')),
            ('company_id', '=', int(company_id))
        ]],
        {'fields': ['start', 'stop']}
    )

    busy_times = [(mexico_tz.localize(datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')),
                   mexico_tz.localize(datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')))
                  for event in events]

    available_slots = []
    current_time = start_dt

    while current_time + timedelta(hours=1) <= end_dt:
        next_time = current_time + timedelta(hours=1)
        is_free = True

        for busy_start, busy_end in busy_times:
            if not (next_time <= busy_start or current_time >= busy_end):
                is_free = False
                break

        if is_free and current_time > datetime.now(mexico_tz):
            available_slots.append({
                'start': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'stop': next_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        current_time = next_time

    return available_slots

def get_events(start_time, end_time, company_id):
    start_dt = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
    end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

    events = models.execute_kw(
        db, uid, password, 'calendar.event', 'search_read', [[
            ('start', '<=', end_dt.strftime('%Y-%m-%d %H:%M:%S')),
            ('stop', '>=', start_dt.strftime('%Y-%m-%d %H:%M:%S')),
            ('company_id', '=', int(company_id))
        ]],
        {'fields': ['id', 'name', 'start', 'stop', 'company_id', 'user_id', 'partner_ids']}
    )

    for event in events:
        event_start_utc = datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')
        event_stop_utc = datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')

        event_start_mx = pytz.utc.localize(event_start_utc).astimezone(mexico_tz)
        event_stop_mx = pytz.utc.localize(event_stop_utc).astimezone(mexico_tz)

        event['start'] = event_start_mx.strftime('%Y-%m-%d %H:%M:%S')
        event['stop'] = event_stop_mx.strftime('%Y-%m-%d %H:%M:%S')

    return events
