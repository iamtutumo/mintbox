{
    'name': 'CRM Lead Stage Tracking',
    'version': '1.0',
    'category': 'CRM',
    'summary': 'Track lead stage durations and send notifications for overstaying',
    'description': """
        This module extends Odoo CRM to track how long leads stay in each stage.
        Features:
        - Store timestamps on stage changes
        - Computed field for days in current stage
        - Daily scheduled check for overstaying leads
        - Email notifications to HR/CRM Managers
    """,
    'author': 'Surepay Limited',
    'license': 'LGPL-3',
    'website': 'https://surepayltd.com',
    'depends': ['crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/mail_template.xml',
        'views/crm_lead_views.xml',
        'views/crm_lead_stage_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}