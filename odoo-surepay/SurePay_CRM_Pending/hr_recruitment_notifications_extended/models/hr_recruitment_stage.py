# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    # Email notification settings
    send_email_on_enter = fields.Boolean(
        string='Send Email on Stage Entry',
        default=False,
        help='Automatically send email when applicant enters this stage'
    )
    
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain="[('model', '=', 'hr.applicant')]",
        help='Email template to use when applicant enters this stage'
    )
    
    email_description = fields.Text(
        string='Email Description',
        help='Description of what email will be sent'
    )
