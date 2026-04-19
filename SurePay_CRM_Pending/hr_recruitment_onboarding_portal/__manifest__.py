# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment - Onboarding Portal',
    'version': '17.0.1.0.0',
    'summary': 'Complete onboarding system for hired candidates',
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'depends': ['hr_recruitment', 'hr', 'hr_contract', 'website', 'hr_applicant_tracking_random', 'hr_recruitment_stages_surepay'],
    'data': [
        'security/ir.model.access.csv',
        'data/onboarding_task_data.xml',
        'views/hr_applicant_onboarding_views.xml',
        'views/hr_applicant_views.xml',
        'views/website_onboarding_portal.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
