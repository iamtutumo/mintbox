{
    'name': 'SurePay CRM Extension',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'Extends CRM with SurePay specific stages and fields',
    'description': """
        This module extends the Odoo CRM module to include:
        - Custom sales stages for SurePay (Cold Lead, Prospecting, Preparation, Closing, Won, Lost)
        - School code field for leads
        - Cold lead management
        - Stage visibility filtering
        - Kanban view customization
    """,
    'author': 'SurePay',
    'website': 'https://www.surepay.com',
    'depends': [
        'crm',
        'base',
        'website',
        'auth_oauth',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/crm_stage_views.xml',
        'views/referral_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'post_init_hook': 'cleanup_activities',
}
