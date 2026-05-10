{
    'name': 'Client Assessment Form Generator',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'Generate client assessment forms from CRM leads',
    'description': """
        This module adds a button to CRM leads to generate client assessment forms
        using a Word template and save them as attachments.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'crm',
        'web',
        'crm_client_assessment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['docxtpl'],
    },
}
