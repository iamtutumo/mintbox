# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment - Evaluation System',
    'version': '17.0.1.0.0',
    'summary': 'Multi-reviewer scoring and interview management',
    'description': """
        Recruitment Evaluation System
        ==============================
        
        Multi-reviewer scoring and interview management system for recruitment.
        
        Features:
        - Multi-reviewer evaluations (Department Head, HR, CEO)
        - Scoring system (Technical, Cultural Fit, Communication)
        - Overall score calculation with weights
        - Recommendation tracking
        - Interview notes and feedback
        - Panel evaluation support
        - Test results attachment
        - Evaluation reports and summaries
        
        Reviewer Roles:
        - Department Head: Can evaluate applicants in their department
        - HR: Can evaluate all applicants
        - CEO: Can view all evaluations
        
        Scoring Criteria:
        - Technical Skills (0-10)
        - Cultural Fit (0-10)
        - Communication Skills (0-10)
        - Overall Score (weighted average)
        - Recommendation (Strongly Recommend, Recommend, Neutral, Not Recommend)
    """,
    'category': 'Human Resources/Recruitment',
    'author': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'depends': [
        'hr_recruitment',
        'hr_applicant_tracking_random',
        'mail',  # For chatter and activity tracking
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/evaluation_security.xml',
        'wizard/evaluation_wizard_views.xml',
        'views/hr_applicant_evaluation_views.xml',
        'views/hr_applicant_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
