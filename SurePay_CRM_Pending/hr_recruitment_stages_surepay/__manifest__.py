# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment - SurePay Custom Stages',
    'version': '17.0.1.0.0',
    'summary': 'Custom recruitment stages for SurePay workflow',
    'description': """
        Custom Recruitment Stages for SurePay Ltd
        ==========================================
        
        This module adds custom recruitment stages tailored to SurePay's 
        recruitment workflow:
        
        1. Application Received
        2. Eligibility Screening
        3. Shortlisting
        4. Committee Review
        5. Interview
        6. Committee Final Review
        7. Offer
        8. Onboarding
        9. Rejected
        
        Features:
        - Pre-configured stages with proper sequencing
        - Updated status history mapping
        - Integration with applicant tracking system
    """,
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'depends': [
        'hr_recruitment',
        'hr_applicant_tracking_random',
    ],
    'auto_install': True,  # This ensures the module is installed right after hr_recruitment
    'sequence': 1,  # Lower numbers are loaded first
    'post_init_hook': 'post_init_hook',
    'data': [
        'data/hr_recruitment_stage_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
