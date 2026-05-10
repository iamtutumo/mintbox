# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    # Application Summary
    application_summary = fields.Text(
        string='Application Summary',
        help='Brief summary of the applicant and their qualifications'
    )
    
    # Cover Letter
    cover_letter = fields.Html(
        string='Cover Letter',
        help='Applicant cover letter or motivation letter'
    )
    
    # Education
    education_ids = fields.One2many(
        'hr.applicant.education',
        'applicant_id',
        string='Education History'
    )
    
    education_count = fields.Integer(
        string='Education Count',
        compute='_compute_education_count'
    )
    
    highest_education = fields.Char(
        string='Highest Education',
        compute='_compute_highest_education',
        store=True
    )
    
    # Work Experience
    experience_ids = fields.One2many(
        'hr.applicant.experience',
        'applicant_id',
        string='Work Experience'
    )
    
    experience_count = fields.Integer(
        string='Experience Count',
        compute='_compute_experience_count'
    )
    
    total_experience_years = fields.Float(
        string='Total Experience (Years)',
        compute='_compute_total_experience',
        store=True,
        help='Total years of work experience'
    )
    
    # Skills (using Odoo's hr_skills module)
    skill_ids = fields.Many2many(
        'hr.skill',
        'applicant_skill_rel',
        'applicant_id',
        'skill_id',
        string='Skills'
    )
    
    skill_count = fields.Integer(
        string='Skills Count',
        compute='_compute_skill_count'
    )
    
    # Referees
    referee_ids = fields.One2many(
        'hr.applicant.referee',
        'applicant_id',
        string='Referees/References'
    )
    
    referee_count = fields.Integer(
        string='Referee Count',
        compute='_compute_referee_count'
    )
    
    # Computed Fields
    @api.depends('education_ids')
    def _compute_education_count(self):
        for applicant in self:
            applicant.education_count = len(applicant.education_ids)
    
    @api.depends('education_ids', 'education_ids.degree', 'education_ids.year_completed')
    def _compute_highest_education(self):
        for applicant in self:
            if applicant.education_ids:
                # Get most recent education
                latest = applicant.education_ids.sorted(
                    key=lambda x: x.year_completed or 0, 
                    reverse=True
                )[0]
                applicant.highest_education = latest.degree
            else:
                applicant.highest_education = False
    
    @api.depends('experience_ids')
    def _compute_experience_count(self):
        for applicant in self:
            applicant.experience_count = len(applicant.experience_ids)
    
    @api.depends('experience_ids', 'experience_ids.duration_months')
    def _compute_total_experience(self):
        for applicant in self:
            total_months = sum(applicant.experience_ids.mapped('duration_months'))
            applicant.total_experience_years = round(total_months / 12, 1)
    
    @api.depends('skill_ids')
    def _compute_skill_count(self):
        for applicant in self:
            applicant.skill_count = len(applicant.skill_ids)
    
    @api.depends('referee_ids')
    def _compute_referee_count(self):
        for applicant in self:
            applicant.referee_count = len(applicant.referee_ids)
    
    # Smart Button Actions
    def action_view_education(self):
        """Open education records"""
        self.ensure_one()
        return {
            'name': _('Education History'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant.education',
            'view_mode': 'tree,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {'default_applicant_id': self.id},
        }
    
    def action_view_experience(self):
        """Open experience records"""
        self.ensure_one()
        return {
            'name': _('Work Experience'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant.experience',
            'view_mode': 'tree,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {'default_applicant_id': self.id},
        }
    
    def action_view_referees(self):
        """Open referee records"""
        self.ensure_one()
        return {
            'name': _('Referees'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant.referee',
            'view_mode': 'tree,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {'default_applicant_id': self.id},
        }
