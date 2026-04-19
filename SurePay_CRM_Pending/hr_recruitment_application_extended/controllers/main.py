# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.hr_applicant_tracking_random.controllers.main import WebsiteHrRecruitmentTracking
import json

class JobApplicationControllerExtended(WebsiteHrRecruitmentTracking):
    
    @http.route(['/jobs/apply/<model("hr.job"):job>'], type='http', auth="public", website=True, sitemap=True)
    def jobs_apply(self, job, **kwargs):
        """Override the standard jobs_apply to handle extended form submission"""
        
        # If this is a POST request, handle the extended form submission
        if request.httprequest.method == 'POST':
            return self.job_application_submit(**kwargs)
        
        # For GET requests, display the extended form
        # Get all skills for the skills dropdown
        skills = request.env['hr.skill'].sudo().search([])
        
        values = {
            'job': job,
            'skills': skills,
            'error': kwargs.get('error', {}),
            'form_data': kwargs.get('form_data', {}),
        }
        
        return request.render('hr_recruitment_application_extended.job_application_form_template', values)

    def job_application_submit(self, **post):
        """Handle job application form submission"""
        
        # Validate required fields
        required_fields = ['partner_name', 'email_from', 'job_id']
        error = {}
        
        for field in required_fields:
            if not post.get(field):
                error[field] = 'This field is required'
        
        if error:
            return request.redirect('/jobs/apply/%s?error=%s' % (post.get('job_id', ''), json.dumps(error)))
        
        try:
            # Get job and department information
            job_id = int(post.get('job_id'))
            job = request.env['hr.job'].sudo().browse(job_id)
            
            # Create applicant
            applicant_vals = {
                'partner_name': post.get('partner_name'),
                'email_from': post.get('email_from'),
                'partner_phone': post.get('partner_phone'),
                'partner_mobile': post.get('partner_mobile'),
                'job_id': job_id,
                'department_id': job.department_id.id if job.department_id else False,
                'company_id': job.company_id.id if job.company_id else False,
                'name': 'Application for %s' % post.get('job_name', ''),
                'application_summary': post.get('application_summary', ''),
                'cover_letter': post.get('cover_letter', ''),
            }
            
            applicant = request.env['hr.applicant'].sudo().create(applicant_vals)
            
            # Add Education entries
            education_count = int(post.get('education_count', 0))
            for i in range(education_count):
                if post.get(f'education_degree_{i}'):
                    education_vals = {
                        'applicant_id': applicant.id,
                        'degree': post.get(f'education_degree_{i}'),
                        'institution': post.get(f'education_institution_{i}'),
                        'field_of_study': post.get(f'education_field_{i}'),
                        'year_completed': int(post.get(f'education_year_{i}')) if post.get(f'education_year_{i}') else False,
                        'grade': post.get(f'education_grade_{i}'),
                        'currently_studying': post.get(f'education_current_{i}') == 'on',
                    }
                    request.env['hr.applicant.education'].sudo().create(education_vals)
            
            # Add Experience entries
            experience_count = int(post.get('experience_count', 0))
            for i in range(experience_count):
                if post.get(f'experience_position_{i}'):
                    experience_vals = {
                        'applicant_id': applicant.id,
                        'position': post.get(f'experience_position_{i}'),
                        'company': post.get(f'experience_company_{i}'),
                        'start_date': post.get(f'experience_start_{i}'),
                        'end_date': post.get(f'experience_end_{i}') if post.get(f'experience_current_{i}') != 'on' else False,
                        'currently_working': post.get(f'experience_current_{i}') == 'on',
                        'responsibilities': post.get(f'experience_responsibilities_{i}'),
                        'achievements': post.get(f'experience_achievements_{i}'),
                    }
                    request.env['hr.applicant.experience'].sudo().create(experience_vals)
            
            # Add Skills
            skill_ids = request.httprequest.form.getlist('skill_ids')
            if skill_ids:
                try:
                    skill_id_ints = [int(sid) for sid in skill_ids if sid]
                    if skill_id_ints:
                        applicant.sudo().write({'skill_ids': [(6, 0, skill_id_ints)]})
                except Exception as skill_error:
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.warning(f'Failed to save skills: {str(skill_error)}')
            
            # Add Referee entries
            referee_count = int(post.get('referee_count', 0))
            for i in range(referee_count):
                referee_name = post.get(f'referee_name_{i}', '').strip()
                referee_email = post.get(f'referee_email_{i}', '').strip()
                referee_phone = post.get(f'referee_phone_{i}', '').strip()
                
                # Only create referee if at least name, email, and phone are provided
                if referee_name and referee_email and referee_phone:
                    try:
                        referee_vals = {
                            'applicant_id': applicant.id,
                            'name': referee_name,
                            'position': post.get(f'referee_position_{i}', ''),
                            'company': post.get(f'referee_company_{i}', ''),
                            'relationship': post.get(f'referee_relationship_{i}', 'other'),
                            'email': referee_email,
                            'phone': referee_phone,
                            'years_known': int(post.get(f'referee_years_{i}')) if post.get(f'referee_years_{i}') else 0,
                            'can_contact': post.get(f'referee_can_contact_{i}') == 'on',
                        }
                        request.env['hr.applicant.referee'].sudo().create(referee_vals)
                    except Exception as referee_error:
                        import logging
                        _logger = logging.getLogger(__name__)
                        _logger.warning(f'Failed to create referee {i}: {str(referee_error)}')
            
            # Send tracking link email automatically
            try:
                mail_template = request.env.ref('hr_applicant_tracking_random.email_applicant_tracking_link')
                if mail_template and applicant.email_from:
                    mail_template.sudo().send_mail(applicant.id, force_send=True)
            except Exception as email_error:
                # Log the error but don't fail the application submission
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f'Failed to send tracking email to {applicant.email_from}: {str(email_error)}')
            
            # Redirect to success page with tracking ID and applicant info
            return request.redirect('/jobs/apply/success?tracking_id=%s&applicant_id=%s' % (applicant.tracking_id, applicant.id))
            
        except Exception as e:
            error['general'] = str(e)
            return request.redirect('/jobs/apply/%s?error=%s' % (post.get('job_id', ''), json.dumps(error)))

    @http.route('/jobs/apply/success', type='http', auth='public', website=True)
    def job_application_success(self, tracking_id=None, applicant_id=None, **kwargs):
        """Display application success page"""
        
        applicant = None
        if tracking_id:
            applicant = request.env['hr.applicant'].sudo().search([('tracking_id', '=', tracking_id)], limit=1)
        elif applicant_id:
            applicant = request.env['hr.applicant'].sudo().browse(int(applicant_id))
        
        values = {
            'tracking_id': tracking_id or (applicant.tracking_id if applicant else None),
            'applicant': applicant,
            'success': True if applicant else False,
        }
        
        return request.render('hr_recruitment_application_extended.job_application_success_template', values)
