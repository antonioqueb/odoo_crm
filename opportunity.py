from flask import jsonify, request
from datetime import datetime
import pytz
import traceback
import sys

def create_opportunity(models, db, uid, password, mexico_tz):
    try:
        # Obtener datos de la solicitud
        data = request.json
        print(f"Datos recibidos en la API: {data}")  # Verificar datos recibidos
        sys.stdout.flush()

        # Campos requeridos
        required_fields = ['name', 'partner_id', 'partner_name', 'partner_email', 'user_id', 'stage_id', 'expected_revenue', 'probability', 'company_id', 'start_time', 'end_time', 'phone']
        
        # Verificar si faltan campos requeridos
        missing_fields = [f for f in required_fields if not data.get(f) and f != 'partner_id']  # 'partner_id' puede faltar
        if missing_fields:
            print(f"Faltan los siguientes campos: {', '.join(missing_fields)}")
            sys.stdout.flush()
            return jsonify({'status': 'error', 'message': f'Faltan los siguientes campos: {", ".join(missing_fields)}'}), 400
        
        # Desempaquetar datos
        name, partner_id, partner_name, partner_email, user_id, stage_id, expected_revenue, probability, company_id, start_time, end_time, phone = (data.get(f) for f in required_fields)

        # Crear partner si no existe
        if not partner_id and partner_name and partner_email:
            print("Intentando crear el partner...")
            sys.stdout.flush()
            try:
                # Crear el nuevo partner si no existe
                partner_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{'name': partner_name, 'email': partner_email, 'phone': phone}])
                print(f"Partner creado con ID: {partner_id}")
            except Exception as e:
                print(f"Error al crear el partner: {str(e)}")
                sys.stdout.flush()
                return jsonify({'status': 'error', 'message': f'Error al crear el partner: {str(e)}'}), 500
            sys.stdout.flush()

        # Convertir los tiempos a UTC
        try:
            start_time_utc, end_time_utc = (mexico_tz.localize(datetime.strptime(t, '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc) for t in [start_time, end_time])
            print(f"Fechas convertidas a UTC: {start_time_utc}, {end_time_utc}")
            sys.stdout.flush()
        except ValueError as e:
            print(f"Error en la conversión de fechas: {str(e)}")
            sys.stdout.flush()
            return jsonify({'status': 'error', 'message': f'Error en la conversión de fechas: {str(e)}'}), 400

        # Crear la oportunidad
        try:
            opportunity_id = models.execute_kw(db, uid, password, 'crm.lead', 'create', [{
                'name': name, 'partner_id': partner_id, 'user_id': user_id, 'stage_id': stage_id, 'expected_revenue': expected_revenue, 'probability': probability, 'company_id': company_id, 'phone': phone
            }])
            print(f"Oportunidad creada con ID: {opportunity_id}")
            sys.stdout.flush()

            if not opportunity_id:
                print(f"Error: La creación de la oportunidad devolvió un valor nulo.")
                sys.stdout.flush()
                return jsonify({'status': 'error', 'message': 'Error al crear la oportunidad.'}), 500
        except Exception as e:
            print(f"Error al crear la oportunidad: {str(e)}")
            sys.stdout.flush()
            return jsonify({'status': 'error', 'message': f'Error al crear la oportunidad: {str(e)}'}), 500

        # Preparar datos del evento de calendario
        event_data = {
            'name': f'Consultoría para {partner_name}', 
            'start': start_time_utc.strftime('%Y-%m-%d %H:%M:%S'), 
            'stop': end_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id, 
            'partner_ids': [(6, 0, [partner_id])], 
            'company_id': company_id
        }

        # Comprobar si el evento ya está reservado
        try:
            events = models.execute_kw(db, uid, password, 'calendar.event', 'search_count', [[
                ('start', '<=', end_time_utc.strftime('%Y-%m-%d %H:%M:%S')), ('stop', '>=', start_time_utc.strftime('%Y-%m-%d %H:%M:%S'))
            ]])
            print(f"Eventos coincidentes encontrados: {events}")
            sys.stdout.flush()
        except Exception as e:
            print(f"Error al buscar eventos coincidentes: {str(e)}")
            sys.stdout.flush()
            return jsonify({'status': 'error', 'message': f'Error al buscar eventos coincidentes: {str(e)}'}), 500

        if events == 0:
            try:
                event_id = models.execute_kw(db, uid, password, 'calendar.event', 'create', [event_data])
                print(f"Evento de calendario creado con ID: {event_id}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error al crear el evento de calendario: {str(e)}")
                sys.stdout.flush()
                return jsonify({'status': 'error', 'message': f'Error al crear el evento de calendario: {str(e)}'}), 500
        else:
            print("Este horario ya está reservado para otro evento.")
            sys.stdout.flush()
            return jsonify({'status': 'error', 'message': 'Este horario ya está reservado para otro evento en la misma empresa.'}), 400

        # Respuesta de éxito
        return jsonify({'status': 'success', 'opportunity_id': opportunity_id}), 201

    except Exception as e:
        print(f"Error general: {traceback.format_exc()}")
        sys.stdout.flush()
        return jsonify({'status': 'error', 'message': str(e)}), 500
