from config import models, db, uid, password
from utils.time_utils import local_to_utc
import pytz
from datetime import datetime, timedelta

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
    
    # Crear partner si no existe
    if not partner_id and partner_name and partner_email:
        partner_id = models.execute_kw(
            db, uid, password, 'res.partner', 'create', [{
                'name': partner_name,
                'email': partner_email,
                'phone': phone,
            }]
        )

    # Convertir las horas locales a UTC
    start_time_utc = local_to_utc(start_time)
    end_time_utc = local_to_utc(end_time)

    # Crear la oportunidad en Odoo
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

    # Crear un evento relacionado si no hay solapamiento
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
    # Implementación completa para obtener slots disponibles
    pass

def get_events(start_time, end_time, company_id):
    # Implementación completa para obtener eventos desde Odoo
    pass
