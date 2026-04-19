# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment - Analytics Dashboard',
    'version': '17.0.1.0.0',
    'summary': 'Recruitment metrics and analytics dashboard',
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'depends': ['hr_recruitment', 'hr_applicant_tracking_random', 'hr_recruitment_stages_surepay'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_recruitment_dashboard_views.xml',
        'report/recruitment_report_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
