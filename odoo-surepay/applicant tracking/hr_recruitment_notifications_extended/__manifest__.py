# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment - Extended Notifications',
    'version': '17.0.1.0.0',
    'summary': 'Comprehensive email notification system for recruitment',
    'description': """
        Extended Notifications for Recruitment
        =======================================
        
        This module provides a comprehensive email notification system for
        the recruitment process with automated stage-based communications.
        
        Features:
        - Application Received Confirmation
        - Eligibility Screening Rejection (Template 1)
        - Post-Shortlisting Rejection (Template 2)
        - Interview Invitation
        - Offer Letter
        - Onboarding Invitation
        - Stage Change Notifications
        - Configurable email templates per stage
        - Automated email triggers
        
        Email Templates:
        1. Application Received
        2. Eligibility Rejection
        3. Shortlisting Rejection
        4. Interview Scheduled
        5. Offer Extended
        6. Onboarding Welcome
        7. Generic Stage Change
    """,
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'depends': [
        'hr_recruitment',
        'hr_applicant_tracking_random',
        'hr_recruitment_stages_surepay',
    ],
    'data': [
        'data/minimal_template_fixed.xml',  # Using the fixed minimal template
        'views/hr_recruitment_stage_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
