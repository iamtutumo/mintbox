# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment - Extended Application Form',
    'version': '17.0.1.0.1',
    'summary': 'Extended application form with education, experience, skills, and referees',
    'description': """
        Extended Application Form for Recruitment
        ==========================================
        
        This module extends the standard HR recruitment application form with
        comprehensive candidate information fields:
        
        Features:
        - Cover Letter (rich text field)
        - Education History (multiple qualifications)
        - Work Experience (multiple positions with details)
        - Skills (tagging system)
        - Referees (multiple references with contact details)
        - Public Application Web Form
        - Auto-population to HR module
        
        New Models:
        - hr.applicant.education
        - hr.applicant.experience
        - hr.applicant.referee
        - hr.skill (if not exists)
        
        Extended Models:
        - hr.applicant (with new One2many and Many2many fields)
    """,
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'depends': [
        'hr_recruitment',
        'hr_applicant_tracking_random',
        'website',
        'hr_skills',  # Odoo standard skills module
        'mail',  # For chatter and activity tracking
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_applicant_views.xml',
        'views/hr_applicant_education_views.xml',
        'views/hr_applicant_experience_views.xml',
        'views/hr_applicant_referee_views.xml',
        'views/website_application_form.xml',
        'views/website_header.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
