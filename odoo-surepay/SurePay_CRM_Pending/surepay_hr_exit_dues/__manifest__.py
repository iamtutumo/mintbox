{
    'name': 'SurePay HR Exit Dues',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manages employee exit dues and settlements',
    'description': """
        This module manages employee exit dues and settlements:
        - Shows pending dues on employee exit (salary balance, advances, loans)
        - Dedicated Exit Dues tab on employee form
        - Exportable report for exit dues by department
    """,
    'author': 'SurePay',
    'website': 'https://www.surepay.com',
    'depends': [
        'hr',
        'surepay_payroll',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/hr_exit_due_views.xml',
        'reports/hr_exit_due_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
