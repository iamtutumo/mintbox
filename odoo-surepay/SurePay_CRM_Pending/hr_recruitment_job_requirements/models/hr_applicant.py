# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    # Screening fields
    screening_status = fields.Selection([
        ('pending', 'Pending Screening'),
        ('passed', 'Passed Screening'),
        ('failed', 'Failed Screening'),
        ('manual', 'Manual Review'),
        ('override', 'Manual Override'),
    ], string='Screening Status', default='pending', tracking=True)
    
    screening_log_ids = fields.One2many(
        'applicant.screening.log',
        'applicant_id',
        string='Screening Logs'
    )
    
    screening_log_count = fields.Integer(
        string='Screening Logs',
        compute='_compute_screening_log_count'
    )
    
    last_screening_date = fields.Datetime(
        string='Last Screened',
        compute='_compute_last_screening_date',
        store=True
    )
    
    @api.depends('screening_log_ids')
    def _compute_screening_log_count(self):
        for applicant in self:
            applicant.screening_log_count = len(applicant.screening_log_ids)
    
    @api.depends('screening_log_ids', 'screening_log_ids.screening_date')
    def _compute_last_screening_date(self):
        for applicant in self:
            if applicant.screening_log_ids:
                applicant.last_screening_date = applicant.screening_log_ids[0].screening_date
            else:
                applicant.last_screening_date = False

    @api.model
    def create(self, vals):
        """Override create to perform auto-screening"""
        applicant = super(HrApplicant, self).create(vals)
        
        # Perform auto-screening if enabled for the job
        if applicant.job_id and applicant.job_id.auto_screen_enabled:
            applicant.perform_eligibility_screening()
        
        return applicant

    def perform_eligibility_screening(self):
        """Perform eligibility screening against job requirements"""
        self.ensure_one()
        
        if not self.job_id:
            return
        
        job = self.job_id
        
        # Initialize screening results
        experience_check = 'na'
        education_check = 'na'
        skills_check = 'na'
        failure_reasons = []
        
        # Check experience requirement
        if job.min_years_experience:
            experience_check, exp_reason = self._check_experience_requirement(job)
            if experience_check == 'fail':
                failure_reasons.append(exp_reason)
        
        # Check education requirement
        if job.required_education_level:
            education_check, edu_reason = self._check_education_requirement(job)
            if education_check == 'fail':
                failure_reasons.append(edu_reason)
        
        # Check skills requirement
        if job.required_skill_ids:
            skills_check, skill_reason = self._check_skills_requirement(job)
            if skills_check == 'fail':
                failure_reasons.append(skill_reason)
        
        # Determine overall result
        checks = [experience_check, education_check, skills_check]
        active_checks = [c for c in checks if c != 'na']
        
        if not active_checks:
            # No requirements set
            screening_result = 'pass'
            screening_status = 'passed'
        elif job.strict_screening:
            # Strict mode: all must pass
            if all(c == 'pass' for c in active_checks):
                screening_result = 'pass'
                screening_status = 'passed'
            else:
                screening_result = 'fail'
                screening_status = 'failed'
        else:
            # Lenient mode: at least one must pass
            if any(c == 'pass' for c in active_checks):
                screening_result = 'pass'
                screening_status = 'passed'
            else:
                screening_result = 'fail'
                screening_status = 'failed'
        
        # Create screening log
        log_vals = {
            'applicant_id': self.id,
            'job_id': job.id,
            'screening_result': screening_result,
            'experience_check': experience_check,
            'education_check': education_check,
            'skills_check': skills_check,
            'applicant_experience_years': self.total_experience_years or 0,
            'required_experience': job.min_years_experience or '',
            'applicant_education': self.highest_education or '',
            'required_education': dict(job._fields['required_education_level'].selection).get(job.required_education_level, ''),
            'applicant_skills_count': len(self.skill_ids),
            'required_skills_count': len(job.required_skill_ids),
            'matching_skills_count': len(self.skill_ids & job.required_skill_ids),
            'failure_reasons': '\n'.join(failure_reasons) if failure_reasons else '',
            'screening_notes': f"Auto-screening performed. Strict mode: {job.strict_screening}",
        }
        
        self.env['applicant.screening.log'].create(log_vals)
        
        # Update applicant screening status
        self.screening_status = screening_status
        
        # If failed, move to rejected stage and send email
        if screening_result == 'fail':
            self._handle_screening_failure()
        
        return screening_result

    def _check_experience_requirement(self, job):
        """Check if applicant meets experience requirement"""
        required = job.min_years_experience
        applicant_years = self.total_experience_years or 0
        
        # Map requirement to minimum years
        experience_map = {
            '0-2': 0,
            '3-5': 3,
            '6-10': 6,
            '10+': 10,
        }
        
        min_required = experience_map.get(required, 0)
        
        if applicant_years >= min_required:
            return 'pass', ''
        else:
            return 'fail', f"Insufficient experience: {applicant_years} years (required: {required})"

    def _check_education_requirement(self, job):
        """Check if applicant meets education requirement"""
        required_level = job.required_education_level
        required_field = job.required_field_of_study
        
        if not self.education_ids:
            return 'fail', "No education records provided"
        
        # Education level hierarchy
        education_hierarchy = {
            'high_school': 1,
            'diploma': 2,
            'bachelor': 3,
            'master': 4,
            'phd': 5,
        }
        
        required_rank = education_hierarchy.get(required_level, 0)
        
        # Check if any education meets the requirement
        for edu in self.education_ids:
            # Simple keyword matching for education level
            degree_lower = edu.degree.lower() if edu.degree else ''
            
            applicant_rank = 0
            if 'phd' in degree_lower or 'doctorate' in degree_lower:
                applicant_rank = 5
            elif 'master' in degree_lower or 'mba' in degree_lower:
                applicant_rank = 4
            elif 'bachelor' in degree_lower or 'degree' in degree_lower:
                applicant_rank = 3
            elif 'diploma' in degree_lower:
                applicant_rank = 2
            elif 'high school' in degree_lower or 'secondary' in degree_lower:
                applicant_rank = 1
            
            # Check if education level is sufficient
            if applicant_rank >= required_rank:
                # If field of study is required, check it
                if required_field:
                    field_lower = edu.field_of_study.lower() if edu.field_of_study else ''
                    if required_field.lower() in field_lower:
                        return 'pass', ''
                else:
                    return 'pass', ''
        
        if required_field:
            return 'fail', f"Education does not match required level ({required_level}) or field ({required_field})"
        else:
            return 'fail', f"Education level below required ({required_level})"

    def _check_skills_requirement(self, job):
        """Check if applicant has required skills"""
        required_skills = job.required_skill_ids
        applicant_skills = self.skill_ids
        min_required = job.min_required_skills or len(required_skills)
        
        if not applicant_skills:
            return 'fail', "No skills provided"
        
        # Find matching skills
        matching_skills = applicant_skills & required_skills
        matching_count = len(matching_skills)
        
        if matching_count >= min_required:
            return 'pass', ''
        else:
            missing = required_skills - applicant_skills
            missing_names = ', '.join(missing.mapped('name'))
            return 'fail', f"Insufficient skills: {matching_count}/{min_required} required skills. Missing: {missing_names}"

    def _handle_screening_failure(self):
        """Handle applicant who failed screening"""
        self.ensure_one()
        
        # Find rejected stage
        rejected_stage = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Rejected'),
            ('fold', '=', True)
        ], limit=1)
        
        if not rejected_stage:
            # Find any folded stage
            rejected_stage = self.env['hr.recruitment.stage'].search([
                ('fold', '=', True)
            ], limit=1)
        
        if rejected_stage:
            # Move to rejected stage
            self.stage_id = rejected_stage.id
            
            # Send eligibility rejection email
            template = self.env.ref(
                'hr_recruitment_notifications_extended.email_eligibility_rejection',
                raise_if_not_found=False
            )
            
            if template and self.email_from:
                try:
                    template.send_mail(self.id, force_send=True, raise_exception=False)
                except Exception as e:
                    _logger.warning('Failed to send eligibility rejection email: %s', str(e))

    def action_view_screening_logs(self):
        """Open screening logs"""
        self.ensure_one()
        return {
            'name': _('Screening Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'applicant.screening.log',
            'view_mode': 'tree,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {'default_applicant_id': self.id},
        }
    
    def action_manual_screening_override(self):
        """Manually override screening result"""
        self.ensure_one()
        self.screening_status = 'override'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Screening Override'),
                'message': _('Screening status manually overridden. Applicant can proceed.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_rescreen_applicant(self):
        """Re-run screening for applicant"""
        self.ensure_one()
        result = self.perform_eligibility_screening()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Screening Complete'),
                'message': _('Applicant re-screened. Result: %s') % result.upper(),
                'type': 'success' if result == 'pass' else 'warning',
                'sticky': False,
            }
        }
