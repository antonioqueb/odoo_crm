# config.py
import os
import xmlrpc.client
import pytz

# Cargar variables de entorno
odoo_url, db, username, password = (
    os.getenv(k) for k in ['ODOO_URL', 'ODOO_DB', 'ODOO_USERNAME', 'ODOO_PASSWORD']
)

# Autenticación con Odoo
common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

# Conexión a los modelos de Odoo
models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

# Zona horaria de México
mexico_tz = pytz.timezone('America/Mexico_City')
