# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    def write(self, vals):
        """Override write to send emails on stage change"""
        # Store old stage for comparison
        old_stages = {applicant.id: applicant.stage_id for applicant in self}
        
        result = super(HrApplicant, self).write(vals)
        
        # Check if stage changed and send email if configured
        if 'stage_id' in vals:
            for applicant in self:
                old_stage = old_stages.get(applicant.id)
                new_stage = applicant.stage_id
                
                # Only send if stage actually changed
                if old_stage != new_stage and new_stage:
                    if new_stage.send_email_on_enter and new_stage.email_template_id:
                        # Check if applicant has email
                        if applicant.email_from:
                            try:
                                new_stage.email_template_id.send_mail(
                                    applicant.id,
                                    force_send=True,
                                    raise_exception=False
                                )
                            except Exception as e:
                                # Log error but don't fail the stage change
                                _logger.warning(
                                    'Failed to send email for applicant %s: %s',
                                    applicant.id, str(e)
                                )
        
        return result

    @api.model
    def create(self, vals):
        """Override create to send application received email"""
        applicant = super(HrApplicant, self).create(vals)
        
        # Send application received confirmation
        if applicant.email_from:
            template = self.env.ref(
                'hr_recruitment_notifications_extended.email_application_received',
                raise_if_not_found=False
            )
            if template:
                try:
                    template.send_mail(applicant.id, force_send=True, raise_exception=False)
                except Exception:
                    pass
        
        return applicant
