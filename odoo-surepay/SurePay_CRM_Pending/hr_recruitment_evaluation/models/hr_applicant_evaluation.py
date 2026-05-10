# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrApplicantEvaluation(models.Model):
    _name = 'hr.applicant.evaluation'
    _description = 'Applicant Evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'evaluation_date desc, id desc'

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
        string='Position',
        related='applicant_id.job_id',
        store=True
    )
    
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewer',
        required=True,
        default=lambda self: self.env.user
    )
    
    reviewer_role = fields.Selection([
        ('dept_head', 'Department Head'),
        ('hr', 'HR'),
        ('ceo', 'CEO/Managing Director'),
        ('panel', 'Panel Member'),
    ], string='Reviewer Role', required=True)
    
    interview_date = fields.Datetime(
        string='Interview Date'
    )
    
    # Scoring (0-10 scale)
    technical_score = fields.Float(
        string='Technical Skills',
        help='Rate technical competency (0-10)'
    )
    
    cultural_fit_score = fields.Float(
        string='Cultural Fit',
        help='Rate alignment with company culture (0-10)'
    )
    
    communication_score = fields.Float(
        string='Communication Skills',
        help='Rate communication ability (0-10)'
    )
    
    # Weights for score calculation
    technical_weight = fields.Float(
        string='Technical Weight',
        default=40.0,
        help='Percentage weight for technical score'
    )
    
    cultural_weight = fields.Float(
        string='Cultural Weight',
        default=30.0,
        help='Percentage weight for cultural fit score'
    )
    
    communication_weight = fields.Float(
        string='Communication Weight',
        default=30.0,
        help='Percentage weight for communication score'
    )
    
    overall_score = fields.Float(
        string='Overall Score',
        compute='_compute_overall_score',
        store=True,
        help='Weighted average of all scores'
    )
    
    recommendation = fields.Selection([
        ('strongly_recommend', 'Strongly Recommend'),
        ('recommend', 'Recommend'),
        ('neutral', 'Neutral'),
        ('not_recommend', 'Do Not Recommend'),
    ], string='Recommendation', required=True, tracking=True)
    
    # Detailed feedback
    strengths = fields.Text(
        string='Strengths',
        help='Key strengths observed'
    )
    
    weaknesses = fields.Text(
        string='Areas for Improvement',
        help='Areas where candidate could improve'
    )
    
    notes = fields.Text(
        string='Additional Notes',
        help='Any other observations or comments'
    )
    
    evaluation_date = fields.Datetime(
        string='Evaluation Date',
        default=fields.Datetime.now,
        required=True
    )
    
    # Attachments (test results, etc.)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'evaluation_attachment_rel',
        'evaluation_id',
        'attachment_id',
        string='Attachments'
    )
    
    @api.depends('technical_score', 'cultural_fit_score', 'communication_score',
                 'technical_weight', 'cultural_weight', 'communication_weight')
    def _compute_overall_score(self):
        """Calculate weighted average score"""
        for evaluation in self:
            total_weight = evaluation.technical_weight + evaluation.cultural_weight + evaluation.communication_weight
            if total_weight > 0:
                weighted_sum = (
                    (evaluation.technical_score * evaluation.technical_weight) +
                    (evaluation.cultural_fit_score * evaluation.cultural_weight) +
                    (evaluation.communication_score * evaluation.communication_weight)
                )
                evaluation.overall_score = weighted_sum / total_weight
            else:
                evaluation.overall_score = 0.0
    
    @api.constrains('technical_score', 'cultural_fit_score', 'communication_score')
    def _check_scores(self):
        """Validate scores are between 0 and 10"""
        for evaluation in self:
            if not (0 <= evaluation.technical_score <= 10):
                raise ValidationError(_('Technical score must be between 0 and 10'))
            if not (0 <= evaluation.cultural_fit_score <= 10):
                raise ValidationError(_('Cultural fit score must be between 0 and 10'))
            if not (0 <= evaluation.communication_score <= 10):
                raise ValidationError(_('Communication score must be between 0 and 10'))
    
    @api.constrains('technical_weight', 'cultural_weight', 'communication_weight')
    def _check_weights(self):
        """Validate weights sum to 100"""
        for evaluation in self:
            total = evaluation.technical_weight + evaluation.cultural_weight + evaluation.communication_weight
            if abs(total - 100.0) > 0.01:  # Allow small floating point errors
                raise ValidationError(_('Score weights must sum to 100%'))
    
    def name_get(self):
        """Display name for evaluation"""
        result = []
        for record in self:
            name = f"{record.reviewer_id.name} - {record.applicant_id.partner_name} ({record.overall_score:.1f}/10)"
            result.append((record.id, name))
        return result
