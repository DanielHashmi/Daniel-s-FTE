import xmlrpc.client
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USERNAME')
password = os.getenv('ODOO_PASSWORD')

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# 1. Get a partner (or create one)
partner_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{
    'name': 'SolarSystems Inc.',
    'email': 'finance@solarsystems.example.com'
}])

# 2. Get a product
product_id = models.execute_kw(db, uid, password, 'product.product', 'create', [{
    'name': 'Phase 1: Discovery & Audit',
    'list_price': 15000.0
}])

# 3. Create invoice
invoice_id = models.execute_kw(db, uid, password, 'account.move', 'create', [{
    'move_type': 'out_invoice',
    'partner_id': partner_id,
    'invoice_date': '2026-01-21',
    'invoice_line_ids': [
        (0, 0, {
            'product_id': product_id,
            'quantity': 1,
            'price_unit': 15000.0,
        })
    ]
}])

print(f"Created Draft Invoice ID: {invoice_id}")
