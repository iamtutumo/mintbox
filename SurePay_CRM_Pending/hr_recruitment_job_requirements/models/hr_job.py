# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrJob(models.Model):
    _inherit = 'hr.job'

    # Auto-screening settings
    auto_screen_enabled = fields.Boolean(
        string='Enable Auto-Screening',
        default=False,
        help='Automatically screen applicants against job requirements'
    )
    
    # Experience requirements
    min_years_experience = fields.Selection([
        ('0-2', '0-2 years'),
        ('3-5', '3-5 years'),
        ('6-10', '6-10 years'),
        ('10+', 'More than 10 years'),
    ], string='Minimum Experience Required')
    
    # Education requirements
    required_education_level = fields.Selection([
        ('high_school', 'High School'),
        ('diploma', 'Diploma'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD/Doctorate'),
    ], string='Required Education Level')
    
    required_field_of_study = fields.Char(
        string='Required Field of Study',
        help='e.g., Computer Science, Business Administration'
    )
    
    # Skills requirements
    required_skill_ids = fields.Many2many(
        'hr.skill',
        'job_required_skill_rel',
        'job_id',
        'skill_id',
        string='Required Skills'
    )
    
    min_required_skills = fields.Integer(
        string='Minimum Required Skills',
        default=0,
        help='Minimum number of required skills applicant must have'
    )
    
    # Screening configuration
    strict_screening = fields.Boolean(
        string='Strict Screening',
        default=False,
        help='If enabled, applicant must meet ALL requirements. Otherwise, partial match is acceptable.'
    )
    
    screening_notes = fields.Text(
        string='Screening Notes',
        help='Additional notes about screening criteria'
    )
    
    @api.onchange('required_skill_ids')
    def _onchange_required_skills(self):
        """Auto-set min required skills when skills are selected"""
        if self.required_skill_ids and not self.min_required_skills:
            self.min_required_skills = len(self.required_skill_ids)
