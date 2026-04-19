# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ApplicantStatusHistory(models.Model):
    _name = 'applicant.status.history'
    _description = 'Applicant Status History'
    _order = 'status_date desc, id desc'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', required=True, ondelete='cascade')
    status_date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected')
    ], string='Status', required=True)
    message = fields.Text(string='Message')
    user_id = fields.Many2one('res.users', string='Updated By', default=lambda self: self.env.user)
