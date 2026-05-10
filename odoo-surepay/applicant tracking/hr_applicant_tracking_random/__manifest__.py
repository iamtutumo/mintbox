# -*- coding: utf-8 -*-
{
    'name': 'Applicant Tracking (Random)',
    'version': '17.0.1.0.0',
    'summary': 'Adds public applicant tracking via random tracking ID',
    'description': """
        This module enhances the recruitment process by adding a random tracking ID
        for each applicant, allowing them to check their application status publicly.

        Key Features:
        - Automatic generation of unique tracking IDs for applicants
        - Public status checking via website interface
        - Status history tracking with timestamps and user information
        - Email notifications with tracking links
        - Integration with existing Odoo HR Recruitment module

        Usage Steps:
        1. Install the module from Apps menu
        2. Access "Applicants Tracking" under Recruitment menu
        3. Create applicant records with auto-generated tracking IDs
        4. Update application stages and add status messages
        5. Applicants can check status publicly using /job/status URL
        6. Send tracking links via email using the "Send Link" button
    """,
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'depends': [
        'base',
        'website',
        'hr_recruitment',
        'website_hr_recruitment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_applicant_tracking_views.xml',
        'views/hr_applicant_views.xml',
        'views/website_templates.xml',
        'views/mail_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
