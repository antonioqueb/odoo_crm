from flask import Flask
from flask_cors import CORS
from config import models, db, uid, password, mexico_tz
from eventos import get_events
from slots import available_slots
from opportunity import create_opportunity

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://inventario-plus.gestpro.cloud"}})

routes = [
    ('/create_opportunity', 'POST', create_opportunity),
    ('/available_slots', 'GET', available_slots),
    ('/events', 'GET', get_events)
]

for route, method, func in routes:
    app.route(route, methods=[method])(lambda func=func: func(models, db, uid, password, mexico_tz))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
