{
    'name': 'SurePay Payroll Excel Export',
    'version': '17.0.1.0.0',
    'category': 'Payroll',
    'summary': 'Export and Import payroll data to/from Excel format',
    'description': """
        This module adds comprehensive Excel Export/Import functionality to payroll:
        - Export payslips to Excel with customizable templates
        - Export payroll register by department/period
        - Export payroll summaries and analytics
        - Export employee payroll history
        - Export staff data with editable fields for allowances, fines, salary adjustments
        - Import staff payroll data from Excel with validation
        - Batch payroll processing from imported data
        - Bulk payslip generation and email sending
        - Configurable export/import templates and formats
    """,
    'author': 'SurePay',
    'website': 'https://www.surepay.com',
    'depends': [
        'hr',
        'surepay_payroll',
        'surepay_payroll_fines',
        'mail',
        'web',
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_views.xml',
        'views/hr_payroll_export_views.xml',
        'views/staff_export_template_views.xml',
        'views/staff_import_batch_views.xml',
        'views/staff_import_data_views.xml',
        'views/staff_export_wizard_views.xml',
        'views/staff_import_wizard_views.xml',
        'wizard/payroll_export_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
