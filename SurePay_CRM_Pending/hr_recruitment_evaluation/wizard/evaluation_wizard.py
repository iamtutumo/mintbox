# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class EvaluationWizard(models.TransientModel):
    _name = 'evaluation.wizard'
    _description = 'Evaluation Wizard'

    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        required=True
    )
    
    applicant_name = fields.Char(
        related='applicant_id.partner_name',
        string='Applicant Name'
    )
    
    job_id = fields.Many2one(
        related='applicant_id.job_id',
        string='Position'
    )
    
    reviewer_role = fields.Selection([
        ('dept_head', 'Department Head'),
        ('hr', 'HR'),
        ('ceo', 'CEO/Managing Director'),
        ('panel', 'Panel Member'),
    ], string='Your Role', required=True, default='hr')
    
    interview_date = fields.Datetime(
        string='Interview Date',
        default=fields.Datetime.now
    )
    
    technical_score = fields.Float(
        string='Technical Skills (0-10)',
        default=5.0
    )
    
    cultural_fit_score = fields.Float(
        string='Cultural Fit (0-10)',
        default=5.0
    )
    
    communication_score = fields.Float(
        string='Communication (0-10)',
        default=5.0
    )
    
    recommendation = fields.Selection([
        ('strongly_recommend', 'Strongly Recommend'),
        ('recommend', 'Recommend'),
        ('neutral', 'Neutral'),
        ('not_recommend', 'Do Not Recommend'),
    ], string='Recommendation', required=True, default='neutral')
    
    strengths = fields.Text(string='Strengths')
    weaknesses = fields.Text(string='Areas for Improvement')
    notes = fields.Text(string='Additional Notes')
    
    def action_submit_evaluation(self):
        """Create evaluation and close wizard"""
        self.ensure_one()
        
        self.env['hr.applicant.evaluation'].create({
            'applicant_id': self.applicant_id.id,
            'reviewer_id': self.env.user.id,
            'reviewer_role': self.reviewer_role,
            'interview_date': self.interview_date,
            'technical_score': self.technical_score,
            'cultural_fit_score': self.cultural_fit_score,
            'communication_score': self.communication_score,
            'recommendation': self.recommendation,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'notes': self.notes,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Evaluation Submitted'),
                'message': _('Your evaluation has been recorded successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
