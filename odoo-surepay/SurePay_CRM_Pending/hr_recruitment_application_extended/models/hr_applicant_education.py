# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrApplicantEducation(models.Model):
    _name = 'hr.applicant.education'
    _description = 'Applicant Education History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year_completed desc, id desc'

    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        required=True,
        ondelete='cascade'
    )
    
    degree = fields.Char(
        string='Degree/Certification',
        required=True,
        tracking=True,
        help='e.g., Bachelor of Science, MBA, High School Diploma'
    )
    
    institution = fields.Char(
        string='Institution',
        required=True,
        tracking=True,
        help='Name of school, college, or university'
    )
    
    field_of_study = fields.Char(
        string='Field of Study',
        help='e.g., Computer Science, Business Administration'
    )
    
    year_completed = fields.Integer(
        string='Year Completed',
        help='Year of graduation or completion'
    )
    
    grade = fields.Char(
        string='Grade/GPA',
        help='Final grade or GPA achieved'
    )
    
    currently_studying = fields.Boolean(
        string='Currently Studying',
        default=False
    )
    
    notes = fields.Text(
        string='Additional Notes'
    )

    @api.constrains('year_completed')
    def _check_year_completed(self):
        """Validate year completed is reasonable"""
        for record in self:
            if record.year_completed and not record.currently_studying:
                current_year = fields.Date.today().year
                if record.year_completed > current_year:
                    raise ValidationError(_('Year completed cannot be in the future.'))
                if record.year_completed < 1950:
                    raise ValidationError(_('Please enter a valid year.'))
    
    def name_get(self):
        """Display name for education record"""
        result = []
        for record in self:
            name = f"{record.degree} - {record.institution}"
            if record.year_completed:
                name += f" ({record.year_completed})"
            result.append((record.id, name))
        return result
