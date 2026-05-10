# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class HrApplicantReferee(models.Model):
    _name = 'hr.applicant.referee'
    _description = 'Applicant Referee/Reference'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    name = fields.Char(
        string='Referee Name',
        required=True,
        help='Full name of the referee'
    )
    
    position = fields.Char(
        string='Position/Title',
        help='Job title of the referee'
    )
    
    company = fields.Char(
        string='Company/Organization',
        help='Where the referee works'
    )
    
    relationship = fields.Selection([
        ('supervisor', 'Former Supervisor'),
        ('colleague', 'Former Colleague'),
        ('client', 'Client'),
        ('professor', 'Professor/Teacher'),
        ('other', 'Other')
    ], string='Relationship', default='supervisor')
    
    email = fields.Char(
        string='Email',
        required=True
    )
    
    phone = fields.Char(
        string='Phone Number',
        required=True
    )
    
    years_known = fields.Integer(
        string='Years Known',
        help='How many years have you known this referee?'
    )
    
    can_contact = fields.Boolean(
        string='Can Contact Now',
        default=True,
        help='Is it okay to contact this referee at this time?'
    )
    
    notes = fields.Text(
        string='Additional Notes'
    )
    
    contacted = fields.Boolean(
        string='Contacted',
        default=False,
        help='Has this referee been contacted?'
    )
    
    contacted_date = fields.Date(
        string='Date Contacted'
    )
    
    feedback = fields.Text(
        string='Feedback/Comments',
        help='Feedback received from this referee'
    )
    
    @api.constrains('email')
    def _check_email(self):
        """Validate email format"""
        for record in self:
            if record.email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.email):
                    raise ValidationError(_('Please enter a valid email address.'))
    
    @api.constrains('years_known')
    def _check_years_known(self):
        """Validate years known is reasonable"""
        for record in self:
            if record.years_known and record.years_known < 0:
                raise ValidationError(_('Years known cannot be negative.'))
            if record.years_known and record.years_known > 50:
                raise ValidationError(_('Please enter a reasonable number of years.'))
    
    def name_get(self):
        """Display name for referee record"""
        result = []
        for record in self:
            name = record.name
            if record.company:
                name += f" ({record.company})"
            result.append((record.id, name))
        return result
    
    def action_mark_contacted(self):
        """Mark referee as contacted"""
        self.ensure_one()
        self.write({
            'contacted': True,
            'contacted_date': fields.Date.today()
        })
