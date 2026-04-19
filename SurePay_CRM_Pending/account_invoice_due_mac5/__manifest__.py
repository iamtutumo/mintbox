{
    'name': 'List Due Invoices',
    'version': '17.0.1.1',
    'summary': """Odoo Due Customer Invoices, Odoo Due Vendor Invoices,
Odoo Due Supplier Invoices, Odoo Due Vendor Bills, Odoo Due Invoices""",
    'description': """
List Due Invoices
=================

This module lists (customer or vendor) invoices on or before the due date selected.
""",
    'category': 'Accounting/Accounting',
    'author': 'MAC5',
    'contributors': ['MAC5'],
    'website': 'https://apps.odoo.com/apps/modules/browse?author=MAC5',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_invoice_due_list_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.gif'],
    'support': 'mac5_odoo@outlook.com',
    'license': 'LGPL-3',
    'live_test_url': 'https://www.youtube.com/playlist?list=PLEcsVMEKGyZOD3aqpWh2-bWHBj4g_pBrd',
}
