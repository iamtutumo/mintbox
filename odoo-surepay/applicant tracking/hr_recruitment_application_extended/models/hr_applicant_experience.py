# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrApplicantExperience(models.Model):
    _name = 'hr.applicant.experience'
    _description = 'Applicant Work Experience'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        required=True,
        ondelete='cascade'
    )
    
    position = fields.Char(
        string='Position/Job Title',
        required=True,
        tracking=True,
        help='e.g., Software Developer, Marketing Manager'
    )
    
    company = fields.Char(
        string='Company/Organization',
        required=True,
        tracking=True
    )
    
    start_date = fields.Date(
        string='Start Date',
        required=True
    )
    
    end_date = fields.Date(
        string='End Date'
    )
    
    currently_working = fields.Boolean(
        string='Currently Working Here',
        default=False
    )
    
    responsibilities = fields.Text(
        string='Key Responsibilities',
        help='Main duties and responsibilities in this role'
    )
    
    achievements = fields.Text(
        string='Key Achievements',
        help='Notable accomplishments and contributions'
    )
    
    reason_for_leaving = fields.Char(
        string='Reason for Leaving'
    )
    
    duration_months = fields.Integer(
        string='Duration (Months)',
        compute='_compute_duration',
        store=True
    )
    
    @api.depends('start_date', 'end_date', 'currently_working')
    def _compute_duration(self):
        """Calculate duration in months"""
        for record in self:
            if record.start_date:
                end = record.end_date if not record.currently_working else fields.Date.today()
                if end:
                    delta = end - record.start_date
                    record.duration_months = int(delta.days / 30)
                else:
                    record.duration_months = 0
            else:
                record.duration_months = 0
    
    @api.constrains('start_date', 'end_date', 'currently_working')
    def _check_dates(self):
        """Validate date logic"""
        for record in self:
            if record.start_date:
                if record.start_date > fields.Date.today():
                    raise ValidationError(_('Start date cannot be in the future.'))
                
                if not record.currently_working and record.end_date:
                    if record.end_date < record.start_date:
                        raise ValidationError(_('End date cannot be before start date.'))
                    if record.end_date > fields.Date.today():
                        raise ValidationError(_('End date cannot be in the future.'))
    
    @api.onchange('currently_working')
    def _onchange_currently_working(self):
        """Clear end date if currently working"""
        if self.currently_working:
            self.end_date = False
    
    def name_get(self):
        """Display name for experience record"""
        result = []
        for record in self:
            name = f"{record.position} at {record.company}"
            if record.start_date:
                year = record.start_date.year
                name += f" ({year})"
            result.append((record.id, name))
        return result
