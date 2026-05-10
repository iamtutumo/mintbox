{
    'name': 'SurePay HR Probation',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Adds probation tracking to employee profiles',
    'description': """
        This module adds probation tracking functionality to employee profiles:
        - Adds is_probation checkbox to employee profile
        - Green tick visibility in kanban and form views
        - Report for employees currently on probation
    """,
    'author': 'SurePay',
    'website': 'https://www.surepay.com',
    'depends': [
        'hr',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/hr_probation_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
