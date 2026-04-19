{
    'name': 'Enhanced CRM for SurePay',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'Enhanced CRM with role-based access and stage-based forms',
    'description': """
        This module enhances the Odoo CRM with:
        - Role-based access control for leads
        - Custom fields for different product types
        - Stage-based forms for lead progression
    """,
    'author': 'SurePay',
    'website': 'https://www.surepay.com',
    'depends': ['crm', 'base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/crm_stage_data.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}