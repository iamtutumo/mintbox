from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class KYCDocument(models.Model):
    _name = 'surepay.kyc.document'
    _description = 'KYC Document'
    _order = 'uploaded_date desc'

    name = fields.Char('Document Name', required=True)
    file = fields.Binary('File', required=True, attachment=True)
    file_name = fields.Char('File Name')
    description = fields.Text('Description')
    status = fields.Selection([
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending')
    uploaded_by = fields.Many2one('res.users', 'Uploaded By', default=lambda self: self.env.user.id, readonly=True)
    uploaded_date = fields.Datetime('Uploaded Date', default=fields.Datetime.now, readonly=True)
    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', ondelete='cascade')
    
    def action_approve(self):
        self.ensure_one()
        if not self._is_compliance_officer():
            raise UserError('Only Compliance Officers can approve documents.')
        self.status = 'approved'
    
    def action_reject(self):
        self.ensure_one()
        if not self._is_compliance_officer():
            raise UserError('Only Compliance Officers can reject documents.')
        self.status = 'rejected'
    
    def _is_compliance_officer(self):
        return self.env.user.has_group('kyc_documents.group_kyc_compliance_officer')
