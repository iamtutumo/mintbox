# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ApplicantAuditLog(models.Model):
    _name = 'applicant.audit.log'
    _description = 'Applicant Audit Log'
    _order = 'action_date desc, id desc'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', required=True, ondelete='cascade')
    action_type = fields.Selection([
        ('created', 'Created'),
        ('viewed', 'Viewed'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('exported', 'Data Exported'),
        ('anonymized', 'Anonymized'),
        ('email_sent', 'Email Sent'),
    ], string='Action Type', required=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    action_date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    ip_address = fields.Char(string='IP Address')
    details = fields.Text(string='Details')
    
    @api.model
    def log_action(self, applicant_id, action_type, details=None):
        """Create audit log entry"""
        return self.create({
            'applicant_id': applicant_id,
            'action_type': action_type,
            'details': details,
        })
