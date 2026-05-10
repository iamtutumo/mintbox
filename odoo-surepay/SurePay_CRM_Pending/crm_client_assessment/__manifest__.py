{
    'name': 'CRM Client Assessment',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'Extend CRM with Client Assessment functionality',
    'description': """
        This module extends the CRM module by adding a Client Assessment form
        to capture detailed client information during the sales process.
    """,
    'author': 'Surepay Limited',
    'website': 'https://www.surepayltd.com',
    'depends': [
        'crm',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/crm_client_assessment_data.xml',
        'views/crm_lead_views.xml',
        'views/crm_client_assessment_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
