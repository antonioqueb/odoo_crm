import sys
from datetime import datetime

def fetch_events(models, db, uid, password, start_time, end_time, company_id, mexico_tz):
    """
    Obtiene los eventos desde Odoo para una empresa específica en el rango de fechas dado.
    """
    try:
        # Convertir las fechas de string a objetos datetime en la zona horaria de México
        start_dt = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
        end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

        print(f"Consultando eventos de Odoo con: start_time <= {end_time}, stop >= {start_time}, company_id = {company_id}")
        sys.stdout.flush()

        # Buscar eventos en el calendario filtrando por empresa
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_time),
                ('stop', '>=', start_time),
                ('company_id', '=', company_id),
            ]],
            {'fields': ['start', 'stop']}
        )

        print(f"Eventos obtenidos de Odoo: {events}")
        sys.stdout.flush()

        # Verificar si no hay eventos
        if not events:
            print(f"No se encontraron eventos para la empresa {company_id} en el rango {start_time} - {end_time}")
            sys.stdout.flush()

        # Convertir los eventos a objetos datetime
        busy_times = [(mexico_tz.localize(datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')),
                       mexico_tz.localize(datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')))
                      for event in events]

        return busy_times

    except Exception as e:
        # Manejar errores en la obtención de eventos
        print(f"Error al obtener eventos: {str(e)}")
        sys.stdout.flush()
        raise Exception("Error al obtener eventos desde Odoo.")
