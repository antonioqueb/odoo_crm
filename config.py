# config.py

import os
import xmlrpc.client
import pytz

# Variables de entorno
odoo_url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USERNAME')
password = os.getenv('ODOO_PASSWORD')

# Conexión a Odoo
common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

# Zona horaria de México
mexico_tz = pytz.timezone('America/Mexico_City')
