import sys
import os

# Añadir la ruta principal del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_cors import CORS
from routes.opportunity import opportunity_blueprint
from routes.calendar import calendar_blueprint


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "https://inventario-plus.gestpro.cloud"}})

    # Registrar los blueprints
    app.register_blueprint(opportunity_blueprint)
    app.register_blueprint(calendar_blueprint)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
