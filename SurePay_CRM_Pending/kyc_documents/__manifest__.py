{
    'name': 'KYC Documents Management',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'KYC Documents Management for CRM',
    'description': """
        This module adds KYC (Know Your Customer) document management
        functionality to the CRM module, allowing you to track and manage
        customer verification documents.
    """,
    'author': 'Surepay Limited',
    'website': 'https://www.surepayltd.com',
    'depends': [
        'crm_client_assessment',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/kyc_documents_security.xml',
        'views/kyc_document_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
