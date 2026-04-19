{
    'name': 'Risk Register',
    'version': '17.0.1.0.0',
    'summary': 'Comprehensive Risk Management System',
    'description': """
        Risk Register Module
        ===================
        
        This module provides a comprehensive risk management system with:
        - Risk registration and tracking
        - Audit trail for all changes
        - Export functionality (PDF, Excel, CSV)
        - Dashboard with charts and analytics
        - Email notifications on status changes
        - Department-based access control
        - Document attachment support
    """,
    'author': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'license': 'LGPL-3',
    'category': 'Project Management',
    'depends': ['base', 'mail', 'hr', 'web'],
    'data': [
        'security/risk_register_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/risk_register_views.xml',
        'views/risk_dashboard_views.xml',
        'views/risk_register_menu.xml',
        'report/risk_register_report_templates.xml',
    ],
    # 'assets': {
    #     'web.assets_web': [
    #         'risk_register/static/src/js/basic_action.js',
    #     ],
    # },
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
