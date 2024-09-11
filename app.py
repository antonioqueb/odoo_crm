from flask import Flask
from flask_cors import CORS
from config import models, db, uid, password, mexico_tz
from eventos import get_events
from slots import available_slots
from opportunity import create_opportunity

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://inventario-plus.gestpro.cloud"}})

def register_routes():
    routes = [
        ('/create_opportunity', 'POST', create_opportunity, 'opportunity'),
        ('/available_slots', 'GET', available_slots, 'slots'),
        ('/events', 'GET', get_events, 'events')
    ]
    for route, method, func, endpoint in routes:
        app.add_url_rule(route, view_func=lambda func=func: func(models, db, uid, password, mexico_tz), methods=[method], endpoint=endpoint)

register_routes()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
