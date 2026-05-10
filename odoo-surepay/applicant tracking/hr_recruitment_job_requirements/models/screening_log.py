# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ApplicantScreeningLog(models.Model):
    _name = 'applicant.screening.log'
    _description = 'Applicant Screening Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'screening_date desc, id desc'

    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        required=True,
        ondelete='cascade'
    )
    
    applicant_name = fields.Char(
        string='Applicant Name',
        related='applicant_id.partner_name',
        store=True,
        readonly=True
    )
    
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        required=True
    )
    
    screening_date = fields.Datetime(
        string='Screening Date',
        default=fields.Datetime.now,
        required=True
    )
    
    screening_result = fields.Selection([
        ('pass', 'Passed'),
        ('fail', 'Failed'),
        ('manual', 'Manual Review Required'),
    ], string='Result', required=True, tracking=True)
    
    auto_screened = fields.Boolean(
        string='Auto-Screened',
        default=True
    )
    
    # Screening criteria results
    experience_check = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'N/A'),
    ], string='Experience Check', default='na')
    
    education_check = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'N/A'),
    ], string='Education Check', default='na')
    
    skills_check = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'N/A'),
    ], string='Skills Check', default='na')
    
    # Detailed results
    applicant_experience_years = fields.Float(
        string='Applicant Experience (Years)'
    )
    
    required_experience = fields.Char(
        string='Required Experience'
    )
    
    applicant_education = fields.Char(
        string='Applicant Education'
    )
    
    required_education = fields.Char(
        string='Required Education'
    )
    
    applicant_skills_count = fields.Integer(
        string='Applicant Skills Count'
    )
    
    required_skills_count = fields.Integer(
        string='Required Skills Count'
    )
    
    matching_skills_count = fields.Integer(
        string='Matching Skills'
    )
    
    screening_notes = fields.Text(
        string='Screening Notes'
    )
    
    failure_reasons = fields.Text(
        string='Failure Reasons',
        help='Reasons why applicant failed screening'
    )
    
    def name_get(self):
        """Display name for screening log"""
        result = []
        for record in self:
            name = f"{record.applicant_id.partner_name} - {record.screening_result.upper()} ({record.screening_date.strftime('%Y-%m-%d')})"
            result.append((record.id, name))
        return result
