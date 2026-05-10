# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment - Compliance Tools',
    'version': '17.0.1.0.4',
    'summary': 'GDPR compliance and audit trail for recruitment',
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'depends': ['hr_recruitment', 'hr_applicant_tracking_random', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'wizard/gdpr_export_wizard_views.xml',
        'wizard/gdpr_anonymize_wizard_views.xml',
        'views/hr_applicant_views.xml',
        'views/applicant_audit_log_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
