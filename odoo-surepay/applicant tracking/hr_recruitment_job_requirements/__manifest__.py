# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment - Job Requirements & Screening',
    'version': '17.0.1.0.0',
    'summary': 'Automated eligibility screening based on job requirements',
    'description': """
        Job Requirements and Automated Screening
        =========================================
        
        This module enables automated eligibility screening of applicants
        based on predefined job requirements.
        
        Features:
        - Define job requirements (experience, education, skills)
        - Automated eligibility screening on application
        - Auto-rejection of unqualified candidates
        - Screening reports and logs
        - Manual override capability
        - Configurable screening rules per job
        
        Job Requirements:
        - Minimum years of experience (0-2, 3-5, 6-10, 10+)
        - Required education level
        - Required field of study
        - Required skills/certifications
        - Auto-screening toggle
        
        Screening Process:
        1. Applicant submits application
        2. System compares against job requirements
        3. If unqualified, auto-move to "Rejected" stage
        4. Send eligibility rejection email
        5. Log screening decision
    """,
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'depends': [
        'hr_recruitment',
        'hr_applicant_tracking_random',
        'hr_recruitment_application_extended',
        'hr_recruitment_stages_surepay',
        'hr_recruitment_notifications_extended',
        'mail',  # For chatter and activity tracking
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_job_views.xml',
        'views/hr_applicant_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
