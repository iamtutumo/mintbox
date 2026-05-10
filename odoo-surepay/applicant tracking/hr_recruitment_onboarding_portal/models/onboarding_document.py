# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class OnboardingDocument(models.Model):
    _name = 'onboarding.document'
    _description = 'Onboarding Document'
    _order = 'sequence, id'

    onboarding_id = fields.Many2one('hr.applicant.onboarding', string='Onboarding', required=True, ondelete='cascade')
    name = fields.Char(string='Document Name', required=True)
    document_type = fields.Selection([
        ('id', 'ID/Passport'),
        ('tax_pin', 'Tax PIN'),
        ('nssf', 'NSSF Number'),
        ('nhif', 'NHIF Number'),
        ('bank_details', 'Bank Details'),
        ('certificate', 'Certificate/Diploma'),
        ('contract', 'Signed Contract'),
        ('other', 'Other'),
    ], string='Document Type', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    required = fields.Boolean(string='Required', default=True)
    file = fields.Binary(string='File', attachment=True)
    filename = fields.Char(string='Filename')
    uploaded_date = fields.Datetime(string='Upload Date')
    verified = fields.Boolean(string='Verified', default=False)
    verified_by = fields.Many2one('res.users', string='Verified By')
    verified_date = fields.Datetime(string='Verification Date')
    notes = fields.Text(string='Notes')
