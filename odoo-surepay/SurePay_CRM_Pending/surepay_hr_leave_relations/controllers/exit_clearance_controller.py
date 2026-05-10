# -*- coding: utf-8 -*-
from odoo import http, fields, models, _
from odoo.http import request, content_disposition
import base64
import logging

_logger = logging.getLogger(__name__)


class ExitClearanceFormController(http.Controller):
    """HTTP Controller to handle exit clearance form submissions from email forms"""

    @http.route('/exit-clearance/submit-interview', type='http', auth='public', methods=['POST'], csrf=False)
    def submit_exit_interview(self, **kwargs):
        """Handle exit interview form submission from email"""
        try:
            # Extract form data
            clearance_id = kwargs.get('clearance_id')
            security_token = kwargs.get('security_token')
            
            if not clearance_id or not security_token:
                return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                    'error_message': 'Missing required parameters'
                })
            
            # Validate security token
            clearance = request.env['hr.exit.clearance'].sudo().browse(int(clearance_id))
            if not clearance.exists() or clearance.security_token != security_token:
                return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                    'error_message': 'Invalid security token or clearance record'
                })
            
            # Handle signature upload
            employee_signature = None
            if 'employee_signature' in request.httprequest.files:
                signature_file = request.httprequest.files['employee_signature']
                if signature_file and signature_file.filename:
                    employee_signature = base64.b64encode(signature_file.read())
            
            # Update clearance record with interview data
            clearance.write({
                'reason_for_leaving_category': kwargs.get('reason_for_leaving_category'),
                'reason_for_leaving_other': kwargs.get('reason_for_leaving_other'),
                'decision_factors': kwargs.get('decision_factors'),
                'most_satisfying': kwargs.get('most_satisfying'),
                'least_satisfying': kwargs.get('least_satisfying'),
                'job_duties_as_expected': kwargs.get('job_duties_as_expected'),
                'improvement_suggestions': kwargs.get('improvement_suggestions'),
                'would_recommend': kwargs.get('would_recommend') == 'yes',
                'employee_signature': employee_signature,
                'employee_signature_date': fields.Date.today(),
                'exit_interview_completed': True,
                'exit_interview_date': fields.Date.today(),
            })
            
            # Send notification to HR
            clearance._send_clearance_form_email()
            
            return request.render('surepay_hr_leave_relations.exit_clearance_success_template', {
                'message': 'Exit interview submitted successfully. HR has been notified.',
                'employee_name': clearance.employee_id.name
            })
            
        except Exception as e:
            _logger.error(f"Error submitting exit interview: {str(e)}")
            return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                'error_message': f'An error occurred: {str(e)}'
            })

    @http.route('/exit-clearance/submit-department', type='http', auth='public', methods=['POST'], csrf=False)
    def submit_department_clearance(self, **kwargs):
        """Handle department clearance form submission from email"""
        try:
            # Extract form data
            clearance_id = kwargs.get('clearance_id')
            security_token = kwargs.get('security_token')
            department_id = kwargs.get('department_id')
            
            if not clearance_id or not security_token or not department_id:
                return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                    'error_message': 'Missing required parameters'
                })
            
            # Validate security token
            clearance = request.env['hr.exit.clearance'].sudo().browse(int(clearance_id))
            if not clearance.exists() or clearance.security_token != security_token:
                return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                    'error_message': 'Invalid security token or clearance record'
                })
            
            # Find or create clearance line for this department
            department = request.env['hr.department'].sudo().browse(int(department_id))
            clearance_line = clearance.clearance_line_ids.filtered(
                lambda line: line.department_id.id == department.id
            )
            
            if not clearance_line:
                clearance_line = request.env['hr.exit.clearance.line'].sudo().create({
                    'clearance_id': clearance.id,
                    'department_id': department.id,
                    'department_name': department.name,
                })
            
            # Handle signature upload
            manager_signature = None
            if 'manager_signature' in request.httprequest.files:
                signature_file = request.httprequest.files['manager_signature']
                if signature_file and signature_file.filename:
                    manager_signature = base64.b64encode(signature_file.read())
            
            # Update clearance line
            clearance_line.write({
                'status': kwargs.get('clearance_status'),
                'notes': kwargs.get('department_notes'),
                'cleared_by': request.env.user.id if request.env.user else None,
                'clearance_date': fields.Date.today(),
                'manager_signature': manager_signature,
            })
            
            # Handle equipment returns
            equipment_items = kwargs.getlist('equipment_description[]')
            serial_numbers = kwargs.getlist('serial_number[]')
            return_statuses = kwargs.getlist('return_status[]')
            conditions = kwargs.getlist('condition[]')
            equipment_notes = kwargs.getlist('equipment_notes[]')
            
            for i, item_desc in enumerate(equipment_items):
                if item_desc.strip():
                    equipment_data = {
                        'clearance_id': clearance.id,
                        'department_id': department.id,
                        'item_description': item_desc,
                        'serial_number': serial_numbers[i] if i < len(serial_numbers) else '',
                        'status': return_statuses[i] if i < len(return_statuses) else 'not_returned',
                        'condition_on_return': conditions[i] if i < len(conditions) else '',
                        'notes': equipment_notes[i] if i < len(equipment_notes) else '',
                        'date_returned': fields.Date.today() if return_statuses[i] == 'returned' else None,
                    }
                    request.env['hr.exit.clearance.equipment'].sudo().create(equipment_data)
            
            # Send notification to HR
            clearance._send_clearance_form_email()
            
            return request.render('surepay_hr_leave_relations.exit_clearance_success_template', {
                'message': f'{department.name} clearance submitted successfully. HR has been notified.',
                'employee_name': clearance.employee_id.name
            })
            
        except Exception as e:
            _logger.error(f"Error submitting department clearance: {str(e)}")
            return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                'error_message': f'An error occurred: {str(e)}'
            })

    @http.route('/exit-clearance/submit-final', type='http', auth='public', methods=['POST'], csrf=False)
    def submit_final_approval(self, **kwargs):
        """Handle final HR approval form submission"""
        try:
            # Extract form data
            clearance_id = kwargs.get('clearance_id')
            security_token = kwargs.get('security_token')
            
            if not clearance_id or not security_token:
                return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                    'error_message': 'Missing required parameters'
                })
            
            # Validate security token
            clearance = request.env['hr.exit.clearance'].sudo().browse(int(clearance_id))
            if not clearance.exists() or clearance.security_token != security_token:
                return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                    'error_message': 'Invalid security token or clearance record'
                })
            
            # Handle signature upload
            hr_final_signature = None
            if 'hr_final_signature' in request.httprequest.files:
                signature_file = request.httprequest.files['hr_final_signature']
                if signature_file and signature_file.filename:
                    hr_final_signature = base64.b64encode(signature_file.read())
            
            # Update clearance record with final approval data
            clearance.write({
                'final_approval_status': kwargs.get('final_approval_status'),
                'hr_final_notes': kwargs.get('hr_final_notes'),
                'hr_final_signature': hr_final_signature,
                'hr_final_signature_date': fields.Date.today(),
                'state': 'approved' if kwargs.get('final_approval_status') == 'approved' else 'rejected',
            })
            
            # Generate and attach final clearance form
            final_form_content = clearance._generate_hr_final_clearance_form()
            if final_form_content:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': f'Final_Clearance_Form_{clearance.employee_id.name}_{fields.Date.today()}.html',
                    'type': 'binary',
                    'datas': base64.b64encode(final_form_content.encode('utf-8')),
                    'res_model': 'hr.exit.clearance',
                    'res_id': clearance.id,
                    'mimetype': 'text/html',
                })
                clearance.write({
                    'final_clearance_form_attachment_id': attachment.id
                })
            
            # Send final notification to employee and HR
            clearance._send_clearance_form_email()
            
            return request.render('surepay_hr_leave_relations.exit_clearance_success_template', {
                'message': 'Final approval submitted successfully. Exit clearance process completed.',
                'employee_name': clearance.employee_id.name
            })
            
        except Exception as e:
            _logger.error(f"Error submitting final approval: {str(e)}")
            return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                'error_message': f'An error occurred: {str(e)}'
            })

    @http.route('/exit-clearance/approve-department', type='http', auth='public', methods=['GET'], csrf=False)
    def approve_department_clearance(self, **kwargs):
        """Handle quick department approval via unique link"""
        return self._handle_quick_clearance_action('approved', **kwargs)

    @http.route('/exit-clearance/reject-department', type='http', auth='public', methods=['GET'], csrf=False)
    def reject_department_clearance(self, **kwargs):
        """Handle quick department rejection via unique link"""
        return self._handle_quick_clearance_action('rejected', **kwargs)

    def _handle_quick_clearance_action(self, action, **kwargs):
        """Handle quick clearance actions (approve/reject)"""
        try:
            # Extract parameters
            clearance_id = kwargs.get('clearance_id')
            security_token = kwargs.get('security_token')
            department_id = kwargs.get('department_id')
            
            if not clearance_id or not security_token or not department_id:
                return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                    'error_message': 'Missing required parameters'
                })
            
            # Validate security token
            clearance = request.env['hr.exit.clearance'].sudo().browse(int(clearance_id))
            if not clearance.exists() or clearance.security_token != security_token:
                return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                    'error_message': 'Invalid security token or clearance record'
                })
            
            # Find or create clearance line for this department
            department = request.env['hr.department'].sudo().browse(int(department_id))
            clearance_line = clearance.clearance_line_ids.filtered(
                lambda line: line.department_id.id == department.id
            )
            
            if not clearance_line:
                clearance_line = request.env['hr.exit.clearance.line'].sudo().create({
                    'clearance_id': clearance.id,
                    'department_id': department.id,
                    'department_name': department.name,
                })
            
            # Update clearance line with action
            clearance_line.write({
                'status': action,
                'notes': f'Quick {action} via email link',
                'cleared_by': request.env.user.id if request.env.user else None,
                'clearance_date': fields.Date.today(),
            })
            
            # Send notification to HR
            clearance._send_clearance_form_email()
            
            action_text = 'approved' if action == 'approved' else 'rejected'
            return request.render('surepay_hr_leave_relations.exit_clearance_success_template', {
                'message': f'{department.name} clearance {action_text} successfully. HR has been notified.',
                'employee_name': clearance.employee_id.name
            })
            
        except Exception as e:
            _logger.error(f"Error in quick clearance action {action}: {str(e)}")
            return request.render('surepay_hr_leave_relations.exit_clearance_error_template', {
                'error_message': f'An error occurred: {str(e)}'
            })

    @http.route('/exit-clearance/download-form/<int:clearance_id>', type='http', auth='public', methods=['GET'])
    def download_clearance_form(self, clearance_id, **kwargs):
        """Download the final clearance form as HTML attachment"""
        try:
            security_token = kwargs.get('security_token')
            
            clearance = request.env['hr.exit.clearance'].sudo().browse(clearance_id)
            if not clearance.exists():
                return request.not_found()
            
            # Validate security token if provided
            if security_token and clearance.security_token != security_token:
                return request.forbidden()
            
            # Generate final form content
            form_content = clearance._generate_hr_final_clearance_form()
            if not form_content:
                return request.not_found()
            
            # Create response
            filename = f'Final_Clearance_Form_{clearance.employee_id.name}_{fields.Date.today()}.html'
            response = request.make_response(
                form_content,
                headers=[
                    ('Content-Type', 'text/html'),
                    ('Content-Disposition', content_disposition(filename)),
                    ('Content-Length', len(form_content))
                ]
            )
            
            return response
            
        except Exception as e:
            _logger.error(f"Error downloading clearance form: {str(e)}")
            return request.not_found()
