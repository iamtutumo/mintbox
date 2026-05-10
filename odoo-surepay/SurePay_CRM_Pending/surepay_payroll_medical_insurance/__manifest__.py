{
    'name': 'SurePay Payroll Medical Insurance',
    'version': '17.0.1.0.0',
    'category': 'Payroll',
    'summary': 'Add medical insurance benefits to payroll',
    'description': """
        This module adds Medical Insurance functionality to payroll:
        - Configure medical insurance plans and coverage
        - Add medical insurance as employee benefit
        - Calculate insurance contributions (employee + employer)
        - Track medical insurance claims and reimbursements
        - Generate medical insurance reports
        - Integrate with payroll computation
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
        'views/hr_employee_views.xml',
        'views/hr_payslip_views.xml',
        'views/medical_insurance_plan_views.xml',
        'views/medical_insurance_claim_views.xml',
        'views/medical_insurance_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
