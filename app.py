# app.py
from flask import Flask
from flask_cors import CORS
from config import models, db, uid, password, mexico_tz
from eventos import get_events
from slots import available_slots
from free_slots import free_slots  # Importamos la función free_slots
from opportunity import create_opportunity  # Importamos create_opportunity

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": [
            "https://inventario-plus.online", 
            "https://cumplimiento-normativo.inventario-plus.online", 
            "https://implementamos-tu-erp.gestpro.cloud",
            "https://migraciones-erp.gestpro.cloud/"
        ]
    }
})

def register_routes():
    routes = [
        ('/create_opportunity', 'POST', create_opportunity, 'opportunity'),
        ('/available_slots', 'GET', available_slots, 'slots'),
        ('/events', 'GET', get_events, 'events'),
        ('/free_slots', 'GET', free_slots, 'free_slots')  
    ]
    
    for route, method, func, endpoint in routes:
        if endpoint == 'free_slots':
            # Para free_slots solo se pasan 4 argumentos
            app.add_url_rule(
                route, 
                view_func=lambda func=func: func(models, db, uid, password), 
                methods=[method], 
                endpoint=endpoint
            )
        else:
            # Para los demás se pasan 5 argumentos
            app.add_url_rule(
                route, 
                view_func=lambda func=func: func(models, db, uid, password, mexico_tz), 
                methods=[method], 
                endpoint=endpoint
            )

register_routes()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
