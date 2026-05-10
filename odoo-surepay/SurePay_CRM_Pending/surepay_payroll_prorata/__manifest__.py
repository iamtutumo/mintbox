{
    'name': 'SurePay Payroll Prorata Salary',
    'version': '17.0.1.0.0',
    'category': 'Payroll',
    'summary': 'Calculate partial month salary for mid-month joiners/leavers',
    'description': """
        This module adds Prorata Salary functionality to payroll:
        - Calculate partial month salary for employees who join mid-month
        - Calculate partial month salary for employees who leave mid-month
        - Configurable calculation method (daily rate based on working days or calendar days)
        - Automatic prorata calculation in payslip computation
        - Report: prorata salary calculations and adjustments
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
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_prorata_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
