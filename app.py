# app.py

from flask import Flask
from flask_cors import CORS
from config import models, db, uid, password, mexico_tz  # Importamos desde config.py
from eventos import get_events
from slots import available_slots
from opportunity import create_opportunity

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://inventario-plus.gestpro.cloud"}})

# Ruta para crear oportunidades
@app.route('/create_opportunity', methods=['POST'])
def opportunity():
    return create_opportunity(models, db, uid, password, mexico_tz)

# Ruta para obtener slots disponibles
@app.route('/available_slots', methods=['GET'])
def slots():
    return available_slots(models, db, uid, password, mexico_tz)

# Ruta para obtener eventos
@app.route('/events', methods=['GET'])
def events():
    return get_events(models, db, uid, password, mexico_tz)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
