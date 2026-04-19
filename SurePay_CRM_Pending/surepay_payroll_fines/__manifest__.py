{
    'name': 'SurePay Payroll Fines',
    'version': '17.0.1.0.0',
    'category': 'Payroll',
    'summary': 'Adds fine deduction rules for payroll',
    'description': """
        This module adds fine deduction functionality to payroll:
        - Adds deduction rule for fines
        - HR or Manager can assign fines per employee
        - Manual entry or linked to disciplinary actions
        - Deduction appears on payslip under "Fines"
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
        'views/hr_payslip_views.xml',
        'views/hr_fine_views.xml',
        'views/hr_fine_rule_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
