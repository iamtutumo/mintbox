# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    # GDPR Consent
    gdpr_consent = fields.Boolean(string='GDPR Consent', default=False, tracking=True)
    gdpr_consent_date = fields.Datetime(string='Consent Date')
    consent_source = fields.Selection([
        ('web_form', 'Web Form'),
        ('email', 'Email'),
        ('manual', 'Manual'),
    ], string='Consent Source')
    
    # Data Retention
    data_retention_date = fields.Date(string='Data Retention Until', compute='_compute_retention_date', store=True)
    retention_period_days = fields.Integer(string='Retention Period (Days)', default=730)  # 2 years
    
    # Anonymization
    anonymized = fields.Boolean(string='Anonymized', default=False, tracking=True)
    anonymized_date = fields.Datetime(string='Anonymization Date')
    anonymized_by = fields.Many2one('res.users', string='Anonymized By')
    
    # Audit Logs
    audit_log_ids = fields.One2many('applicant.audit.log', 'applicant_id', string='Audit Logs')
    audit_log_count = fields.Integer(string='Audit Log Count', compute='_compute_audit_log_count')
    
    @api.depends('audit_log_ids')
    def _compute_audit_log_count(self):
        """Compute number of audit logs"""
        for applicant in self:
            applicant.audit_log_count = len(applicant.audit_log_ids)
    
    @api.depends('gdpr_consent_date', 'retention_period_days')
    def _compute_retention_date(self):
        for applicant in self:
            if applicant.gdpr_consent_date:
                applicant.data_retention_date = (applicant.gdpr_consent_date + timedelta(days=applicant.retention_period_days)).date()
            else:
                applicant.data_retention_date = False
    
    @api.model
    def create(self, vals):
        """Set consent if from web form"""
        if vals.get('email_from') and not vals.get('gdpr_consent'):
            vals['gdpr_consent'] = True
            vals['gdpr_consent_date'] = fields.Datetime.now()
            vals['consent_source'] = 'web_form'
        
        return super(HrApplicant, self).create(vals)
    
    def action_anonymize_data(self):
        """Anonymize applicant data (GDPR Right to be Forgotten)"""
        self.ensure_one()
        
        if self.anonymized:
            return
        
        # Anonymize personal data
        self.write({
            'partner_name': 'ANONYMIZED',
            'email_from': 'anonymized@example.com',
            'partner_phone': 'ANONYMIZED',
            'partner_mobile': 'ANONYMIZED',
            'description': 'ANONYMIZED',
            'anonymized': True,
            'anonymized_date': fields.Datetime.now(),
            'anonymized_by': self.env.user.id,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Data Anonymized'),
                'message': _('Applicant data has been anonymized successfully.'),
                'type': 'success',
            }
        }
    
    def action_export_data(self):
        """Export applicant data (GDPR Right to Access)"""
        self.ensure_one()
        
        # Open export wizard
        return {
            'name': _('Export Applicant Data'),
            'type': 'ir.actions.act_window',
            'res_model': 'gdpr.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_applicant_id': self.id},
        }
    
    def action_view_audit_logs(self):
        """View audit logs for this applicant"""
        self.ensure_one()
        return {
            'name': _('Audit Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'applicant.audit.log',
            'view_mode': 'tree,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {'default_applicant_id': self.id},
        }
    
    @api.model
    def _cron_check_data_retention(self):
        """Scheduled action to check and anonymize expired records"""
        today = fields.Date.today()
        expired_applicants = self.search([
            ('data_retention_date', '<', today),
            ('anonymized', '=', False),
        ])
        
        for applicant in expired_applicants:
            applicant.action_anonymize_data()
        
        return True
