from odoo import http, _
from odoo.http import request
import json
import logging
import re

_logger = logging.getLogger(__name__)


class ReferralController(http.Controller):
    
    @http.route('/referral/submit', type='json', auth='public', methods=['POST'], csrf=False)
    def submit_referral(self, **kwargs):
        """
        Handle web form referral submission
        """
        try:
            _logger.info("Referral submission started")
            
            # Get JSON data from request
            raw_data = request.httprequest.data
            _logger.info(f"Raw request data: {raw_data}")
            
            data = json.loads(raw_data)
            _logger.info(f"Parsed data: {data}")
            
            # Validate required fields
            required_fields = ['contact_name', 'email_from', 'phone', 'referrer_name', 'referrer_phone']
            missing_fields = []
            
            for field in required_fields:
                if not data.get(field):
                    missing_fields.append(field.replace('_', ' ').title())
            
            if missing_fields:
                missing_fields_str = ', '.join(missing_fields)
                return {
                    'success': False,
                    'message': f'The following fields are required: {missing_fields_str}'
                }
            
            # Validate email format
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if data.get('email_from') and not re.match(email_pattern, data.get('email_from', '')):
                return {
                    'success': False,
                    'message': 'Please enter a valid contact email address'
                }
            
            # Create lead from submission
            _logger.info("Attempting to create lead from submission")
            crm_lead = request.env['crm.lead'].sudo()
            result = crm_lead.create_lead_from_web_submission(data)
            _logger.info(f"Lead creation result: {result}")
            
            return result
            
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error: {str(e)}")
            return {
                'success': False,
                'message': 'Invalid data format. Please ensure you are sending valid JSON.'
            }
        except Exception as e:
            _logger.error(f"Error in referral submission: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @http.route('/referral/form', type='http', auth='public')
    def referral_form(self, **kwargs):
        """
        Render the referral form page
        """
        return request.render('surepay_crm_extension.referral_form_template', {})
    
    @http.route('/referral/thank-you', type='http', auth='public')
    def referral_thank_you(self, **kwargs):
        """
        Render thank you page
        """
        return request.render('surepay_crm_extension.referral_thank_you_template', {})
