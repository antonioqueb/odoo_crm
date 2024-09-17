from flask import jsonify, request
from datetime import datetime
import pytz
from dateutil import parser
import logging

# Configurar el logging
logging.basicConfig(level=logging.DEBUG)

def get_events(models, db, uid, password, mexico_tz):
    try:
        # Obtener parámetros de la solicitud
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        company_id_str = request.args.get('company_id')

        logging.debug(f"Parámetros recibidos: start_time={start_time_str}, end_time={end_time_str}, company_id={company_id_str}")

        if not all([start_time_str, end_time_str, company_id_str]):
            raise ValueError("Los parámetros 'start_time', 'end_time' y 'company_id' son obligatorios.")

        # Parsear fechas recibidas
        start_dt = parser.isoparse(start_time_str)
        end_dt = parser.isoparse(end_time_str)

        # Si las fechas no tienen información de zona horaria, asumir Mexico TZ
        if start_dt.tzinfo is None:
            start_dt = mexico_tz.localize(start_dt)
            logging.debug(f"start_dt localizado a Mexico TZ: {start_dt}")
        else:
            start_dt = start_dt.astimezone(mexico_tz)
            logging.debug(f"start_dt convertido a Mexico TZ: {start_dt}")

        if end_dt.tzinfo is None:
            end_dt = mexico_tz.localize(end_dt)
            logging.debug(f"end_dt localizado a Mexico TZ: {end_dt}")
        else:
            end_dt = end_dt.astimezone(mexico_tz)
            logging.debug(f"end_dt convertido a Mexico TZ: {end_dt}")

        # Convertir las fechas a UTC para la consulta en Odoo
        start_dt_utc = start_dt.astimezone(pytz.utc)
        end_dt_utc = end_dt.astimezone(pytz.utc)

        # Formatear las fechas en UTC para la consulta
        start_str_utc = start_dt_utc.strftime('%Y-%m-%d %H:%M:%S')
        end_str_utc = end_dt_utc.strftime('%Y-%m-%d %H:%M:%S')

        logging.debug(f"Fechas en UTC para consulta a Odoo: start={start_str_utc}, end={end_str_utc}")

        # Buscar eventos en Odoo usando las fechas en UTC
        search_domain = [
            ('start', '<=', end_str_utc),
            ('stop', '>=', start_str_utc),
            ('company_id', '=', int(company_id_str))
        ]

        logging.debug(f"Dominio de búsqueda en Odoo: {search_domain}")

        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [search_domain], 
            {'fields': ['start', 'stop']}
        )

        logging.debug(f"Eventos obtenidos de Odoo: {events}")

        # Convertir las fechas de eventos de UTC a la zona horaria de México
        for event in events:
            event_start_utc = parser.isoparse(event['start']).replace(tzinfo=pytz.utc)
            event_stop_utc = parser.isoparse(event['stop']).replace(tzinfo=pytz.utc)

            logging.debug(f"Evento UTC: inicio={event_start_utc}, fin={event_stop_utc}")

            # Convertir a la zona horaria de México
            event_start_mx = event_start_utc.astimezone(mexico_tz)
            event_stop_mx = event_stop_utc.astimezone(mexico_tz)

            logging.debug(f"Evento México TZ: inicio={event_start_mx}, fin={event_stop_mx}")

            # Actualizar las fechas en formato ISO en la zona horaria de México
            # Realizar la sustitución de '-06:00' por '-00:00'
            start_iso = event_start_mx.isoformat().replace('-06:00', '-00:00')
            stop_iso = event_stop_mx.isoformat().replace('-06:00', '-00:00')

            event.update({
                'start': start_iso,
                'stop': stop_iso
            })

        # Devolver los eventos con las fechas convertidas
        return jsonify({'status': 'success', 'events': events}), 200

    except Exception as e:
        logging.error(f"Error en get_events: {e}")
        # En caso de error, devolver el mensaje de error
        return jsonify({'status': 'error', 'message': str(e)}), 500
