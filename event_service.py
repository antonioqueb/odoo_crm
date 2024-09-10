import sys
from datetime import datetime

def fetch_events(models, db, uid, password, start_time, end_time, mexico_tz):
    """
    Obtiene los eventos desde Odoo para un rango de fechas dado, sin filtrar por empresa o usuario.
    """
    try:
        # Convertir las fechas de string a objetos datetime en la zona horaria de México
        start_dt = mexico_tz.localize(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
        end_dt = mexico_tz.localize(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))

        print(f"Consultando eventos de Odoo con: start_time <= {end_time}, stop >= {start_time}")
        sys.stdout.flush()

        # Buscar eventos en el calendario filtrando solo por rango de fechas
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[
                ('start', '<=', end_time),
                ('stop', '>=', start_time),
            ]],
            {'fields': ['start', 'stop', 'name', 'user_id', 'location', 'description']}
        )

        print(f"Eventos obtenidos de Odoo: {events}")
        sys.stdout.flush()

        # Verificar si no hay eventos
        if not events:
            print(f"No se encontraron eventos en el rango {start_time} - {end_time}")
            sys.stdout.flush()

        # Convertir los eventos a objetos datetime para los tiempos ocupados
        busy_times = [(mexico_tz.localize(datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S')),
                       mexico_tz.localize(datetime.strptime(event['stop'], '%Y-%m-%d %H:%M:%S')))
                      for event in events]

        # Retornar tanto los tiempos ocupados como los eventos completos
        return busy_times, events

    except Exception as e:
        # Manejar errores en la obtención de eventos
        print(f"Error al obtener eventos: {str(e)}")
        sys.stdout.flush()
        raise Exception("Error al obtener eventos desde Odoo.")
