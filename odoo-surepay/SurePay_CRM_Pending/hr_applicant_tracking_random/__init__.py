from . import models
from . import controllers

def post_init_hook(env):
    """Generate tracking IDs for existing applicants after module installation"""
    applicants = env['hr.applicant'].search([('tracking_id', '=', False)])
    
    if applicants:
        for applicant in applicants:
            tracking_id = applicant._generate_tracking_id()
            applicant.write({'tracking_id': tracking_id})
