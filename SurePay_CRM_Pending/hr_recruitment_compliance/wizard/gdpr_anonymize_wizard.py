# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class GdprAnonymizeWizard(models.TransientModel):
    _name = 'gdpr.anonymize.wizard'
    _description = 'GDPR Anonymization Wizard'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', required=True)
    confirm = fields.Boolean(string='I confirm this action cannot be undone')
    reason = fields.Text(string='Reason for Anonymization', required=True)
    
    def action_anonymize(self):
        """Anonymize applicant data"""
        self.ensure_one()
        
        if not self.confirm:
            raise UserError(_('You must confirm that you understand this action cannot be undone.'))
        
        self.applicant_id.action_anonymize_data()
        
        return {'type': 'ir.actions.act_window_close'}
