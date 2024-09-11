import os, xmlrpc.client, pytz

odoo_url, db, username, password = (os.getenv(k) for k in ['ODOO_URL', 'ODOO_DB', 'ODOO_USERNAME', 'ODOO_PASSWORD'])

common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

mexico_tz = pytz.timezone('America/Mexico_City')
