from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    kyc_document_ids = fields.One2many(
        'surepay.kyc.document', 'lead_id', string='KYC Documents')
        
    kyc_documents_count = fields.Integer(
        string='KYC Documents Count', 
        compute='_compute_kyc_documents_count', 
        store=False
    )

    @api.depends('kyc_document_ids')
    def _compute_kyc_documents_count(self):
        for lead in self:
            lead.kyc_documents_count = len(lead.kyc_document_ids)
