# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import base64

class OnboardingPortalController(http.Controller):

    @http.route('/onboarding/<string:token>', type='http', auth='public', website=True)
    def onboarding_dashboard(self, token, **kwargs):
        """Onboarding portal dashboard"""
        onboarding = request.env['hr.applicant.onboarding'].sudo().search([('portal_access_token', '=', token)], limit=1)
        
        if not onboarding:
            return request.render('website.404')
        
        values = {
            'onboarding': onboarding,
            'applicant': onboarding.applicant_id,
        }
        
        return request.render('hr_recruitment_onboarding_portal.onboarding_dashboard_template', values)

    @http.route('/onboarding/<string:token>/upload', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def upload_document(self, token, **post):
        """Handle document upload"""
        onboarding = request.env['hr.applicant.onboarding'].sudo().search([('portal_access_token', '=', token)], limit=1)
        
        if not onboarding:
            return request.redirect('/onboarding/%s?error=invalid_token' % token)
        
        document_id = int(post.get('document_id'))
        document = request.env['onboarding.document'].sudo().browse(document_id)
        
        if document.onboarding_id != onboarding:
            return request.redirect('/onboarding/%s?error=invalid_document' % token)
        
        # Get uploaded file
        uploaded_file = post.get('file')
        if uploaded_file:
            document.write({
                'file': base64.b64encode(uploaded_file.read()),
                'filename': uploaded_file.filename,
                'uploaded_date': fields.Datetime.now(),
            })
        
        return request.redirect('/onboarding/%s?success=document_uploaded' % token)

    @http.route('/onboarding/<string:token>/task/complete', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def complete_task(self, token, **post):
        """Mark task as complete"""
        onboarding = request.env['hr.applicant.onboarding'].sudo().search([('portal_access_token', '=', token)], limit=1)
        
        if not onboarding:
            return request.redirect('/onboarding/%s?error=invalid_token' % token)
        
        task_id = int(post.get('task_id'))
        task = request.env['onboarding.task.line'].sudo().browse(task_id)
        
        if task.onboarding_id != onboarding:
            return request.redirect('/onboarding/%s?error=invalid_task' % token)
        
        task.write({
            'completed': True,
            'completed_date': fields.Datetime.now(),
            'notes': post.get('notes', ''),
        })
        
        return request.redirect('/onboarding/%s?success=task_completed' % token)
