# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    def write(self, vals):
        """Override write to track stage changes with updated stage mapping"""
        result = super(HrApplicant, self).write(vals)
        
        # Only create status history if stage_id changed and record is saved
        if 'stage_id' in vals:
            for applicant in self:
                if applicant.id and applicant.stage_id:
                    # Updated stage mapping for SurePay custom stages
                    stage_name_mapping = {
                        'Application Received': 'draft',
                        'Eligibility Screening': 'in_progress',
                        'Shortlisting': 'in_progress',
                        'Committee Review': 'in_progress',
                        'Interview': 'interview',
                        'Committee Final Review': 'in_progress',
                        'Offer': 'offer',
                        'Onboarding': 'hired',
                        'Rejected': 'rejected',
                    }
                    
                    # Get status based on stage name
                    status = stage_name_mapping.get(applicant.stage_id.name, 'in_progress')
                    
                    try:
                        # Create status history entry
                        self.env['applicant.status.history'].create({
                            'applicant_id': applicant.id,
                            'status': status,
                            'message': f'Stage changed to {applicant.stage_id.name}'
                        })
                        
                        # Update last status update
                        applicant.last_status_update = fields.Datetime.now()
                    except Exception:
                        pass
        
        return result
