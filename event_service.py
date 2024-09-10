import sys
from datetime import datetime

def fetch_events(models, db, uid, password, mexico_tz):
    """
    Obtiene todos los eventos desde Odoo y los imprime sin filtrar.
    """
    try:
        print("Consultando todos los eventos de Odoo...")
        sys.stdout.flush()

        # Buscar todos los eventos en el calendario
        events = models.execute_kw(
            db, uid, password, 'calendar.event', 'search_read', [[]],  # Sin filtros
            {'fields': ['name', 'start', 'stop', 'company_id', 'user_id', 'partner_ids', 'description']}
        )

        # Imprimir todos los eventos con todas sus propiedades
        print(f"Todos los eventos obtenidos de Odoo: {events}")
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
