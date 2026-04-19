# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    onboarding_id = fields.Many2one('hr.applicant.onboarding', string='Onboarding')
    onboarding_status = fields.Selection(related='onboarding_id.status', string='Onboarding Status', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', related='onboarding_id.employee_id', store=True)
    
    def write(self, vals):
        """Create onboarding when moved to Onboarding stage"""
        result = super(HrApplicant, self).write(vals)
        
        if 'stage_id' in vals:
            for applicant in self:
                if applicant.stage_id.name == 'Onboarding' and not applicant.onboarding_id:
                    # Create onboarding session
                    onboarding = self.env['hr.applicant.onboarding'].create({
                        'applicant_id': applicant.id,
                        'start_date': fields.Date.today(),
                        'status': 'in_progress',
                    })
                    applicant.onboarding_id = onboarding.id
                    
                    # Send onboarding invitation
                    onboarding.action_send_onboarding_invitation()
        
        return result
    
    def action_view_onboarding(self):
        """Open onboarding record"""
        self.ensure_one()
        if not self.onboarding_id:
            # Create onboarding if doesn't exist
            onboarding = self.env['hr.applicant.onboarding'].create({
                'applicant_id': self.id,
                'start_date': fields.Date.today(),
            })
            self.onboarding_id = onboarding.id
        
        return {
            'name': _('Onboarding'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant.onboarding',
            'res_id': self.onboarding_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
