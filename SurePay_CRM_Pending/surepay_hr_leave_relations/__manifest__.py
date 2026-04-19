{
    'name': 'SurePay HR Leave Relations',
    'version': '17.0.1.0.0',
    'summary': 'HR Leave, Attendance & Employee Relations Management',
    'description': """
        SurePay HR Leave Relations Module
        
        Features:
        1. Leave & Attendance Management
           - Preconfigured leave types: Sick Leave, Maternity Leave (90 days), Paternity Leave
           - Approval workflow: Employee → Employee Manager
           - Restrict probation employees from certain leave types
           - Annual leave allocation: 21 days per employee per year
           - No carry-over to next year
           - Leave balance tracking and reporting
        
        2. Exit Clearance Management
           - Exit clearance with department sign-offs (HR, IT, Finance, Line Manager)
           - Clearance workflow and status tracking
           - Final clearance form generation and email notifications
           - Smart button integration on employee forms
        
        3. Grievance Procedures
           - Grievance management with workflow
           - Link to disciplinary actions
           - Escalation tracking and reporting
        
        Security:
        - Reuses existing Odoo HR groups
        - Proper record rules for data access control
        
        Reporting:
        - Leave balances and usage reports
        - Exit clearance status reports
        - Grievance tracking and SLA reports
        - Export to Excel & PDF
    """,
    'author': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'category': 'Human Resources',
    'depends': ['hr', 'hr_holidays', 'mail', 'surepay_hr_management'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/leave_type_data.xml',
        'data/email_templates.xml',
        'views/hr_leave_views.xml',
        'views/exit_clearance_views.xml',
        'views/grievance_views.xml',
        'views/hr_employee_views.xml',
        'views/menu.xml',
        'views/report_views.xml',
        'views/exit_clearance_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
