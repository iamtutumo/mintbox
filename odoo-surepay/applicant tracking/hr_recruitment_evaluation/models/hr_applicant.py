# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    evaluation_ids = fields.One2many(
        'hr.applicant.evaluation',
        'applicant_id',
        string='Evaluations'
    )
    
    evaluation_count = fields.Integer(
        string='Evaluation Count',
        compute='_compute_evaluation_count'
    )
    
    average_score = fields.Float(
        string='Average Score',
        compute='_compute_average_score',
        store=True,
        help='Average of all evaluation scores'
    )
    
    evaluation_summary = fields.Text(
        string='Evaluation Summary',
        compute='_compute_evaluation_summary'
    )
    
    @api.depends('evaluation_ids')
    def _compute_evaluation_count(self):
        for applicant in self:
            applicant.evaluation_count = len(applicant.evaluation_ids)
    
    @api.depends('evaluation_ids', 'evaluation_ids.overall_score')
    def _compute_average_score(self):
        for applicant in self:
            if applicant.evaluation_ids:
                applicant.average_score = sum(applicant.evaluation_ids.mapped('overall_score')) / len(applicant.evaluation_ids)
            else:
                applicant.average_score = 0.0
    
    @api.depends('evaluation_ids', 'evaluation_ids.recommendation')
    def _compute_evaluation_summary(self):
        for applicant in self:
            if not applicant.evaluation_ids:
                applicant.evaluation_summary = 'No evaluations yet'
            else:
                recommendations = applicant.evaluation_ids.mapped('recommendation')
                strongly_recommend = recommendations.count('strongly_recommend')
                recommend = recommendations.count('recommend')
                neutral = recommendations.count('neutral')
                not_recommend = recommendations.count('not_recommend')
                
                summary = f"Total Evaluations: {len(applicant.evaluation_ids)}\n"
                summary += f"Average Score: {applicant.average_score:.2f}/10\n\n"
                summary += "Recommendations:\n"
                if strongly_recommend:
                    summary += f"  - Strongly Recommend: {strongly_recommend}\n"
                if recommend:
                    summary += f"  - Recommend: {recommend}\n"
                if neutral:
                    summary += f"  - Neutral: {neutral}\n"
                if not_recommend:
                    summary += f"  - Not Recommend: {not_recommend}\n"
                
                applicant.evaluation_summary = summary
    
    def action_view_evaluations(self):
        """Open evaluations"""
        self.ensure_one()
        return {
            'name': _('Evaluations'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant.evaluation',
            'view_mode': 'tree,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {
                'default_applicant_id': self.id,
                'default_job_id': self.job_id.id,
            },
        }
    
    def action_create_evaluation(self):
        """Open evaluation wizard"""
        self.ensure_one()
        return {
            'name': _('Evaluate Applicant'),
            'type': 'ir.actions.act_window',
            'res_model': 'evaluation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_applicant_id': self.id,
            },
        }
