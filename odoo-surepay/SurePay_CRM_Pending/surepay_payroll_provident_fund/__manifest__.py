{
    'name': 'SurePay Payroll Provident Fund',
    'version': '17.0.1.0.0',
    'category': 'Payroll',
    'summary': 'Adds Provident Fund as a payroll deduction',
    'description': """
        This module adds Provident Fund functionality to payroll:
        - Adds Provident Fund as a payroll deduction
        - Configurable % of salary (default 5%)
        - Shown separately from NSSF on payslip
        - Report: provident fund totals per run and per employee
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
        'views/hr_provident_fund_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
