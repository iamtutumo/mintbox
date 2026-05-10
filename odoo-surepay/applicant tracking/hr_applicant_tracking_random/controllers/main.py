# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment

class WebsiteHrRecruitmentTracking(WebsiteHrRecruitment):
    
    # Note: The /jobs/apply route is now handled by hr_recruitment_application_extended module
    # This allows the extended form with education, experience, skills, and referees to be displayed
    
    @http.route('/job/status', type='http', auth="public", website=True, sitemap=True)
    def application_status(self, **post):
        """
        Display a form to check application status and show results if tracking ID is provided
        """
        values = {}
        if post.get('tracking_id'):
            tracking_id = post.get('tracking_id').strip().upper()
            email = post.get('email', '').strip().lower()

            domain = [('tracking_id', '=', tracking_id)]
            if email:
                domain.append(('email_from', '=ilike', email))

            applicant = request.env['hr.applicant'].sudo().search(domain, limit=1)

            if applicant:
                values.update({
                    'applicant': applicant,
                    'status': 'found',
                })
            else:
                values['status'] = 'not_found'

        return request.render('hr_applicant_tracking_random.application_status_page', values)

    @http.route('/applicant/tracking/<string:tracking_id>', type='http', auth="public", website=True, sitemap=True)
    def applicant_tracking_page(self, tracking_id, **kwargs):
        """
        Public page to view applicant status using tracking ID
        """
        tracking_id = tracking_id.strip().upper()
        applicant = request.env['hr.applicant'].sudo().search([('tracking_id', '=', tracking_id)], limit=1)

        if applicant:
            values = {
                'applicant': applicant,
                'status': 'found',
            }
        else:
            values = {
                'status': 'not_found',
            }

        return request.render('hr_applicant_tracking_random.application_status_page', values)
