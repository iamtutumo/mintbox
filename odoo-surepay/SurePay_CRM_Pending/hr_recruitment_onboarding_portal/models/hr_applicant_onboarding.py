# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrApplicantOnboarding(models.Model):
    _name = 'hr.applicant.onboarding'
    _description = 'Applicant Onboarding'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', required=True, ondelete='cascade')
    applicant_name = fields.Char(related='applicant_id.partner_name', string='Applicant Name', store=True)
    job_id = fields.Many2one(related='applicant_id.job_id', string='Position', store=True)
    
    status = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='Status', default='not_started', tracking=True)
    
    start_date = fields.Date(string='Start Date')
    expected_start_date = fields.Date(string='Expected Start Date')
    completion_date = fields.Date(string='Completion Date')
    
    # Tasks
    task_ids = fields.One2many('onboarding.task.line', 'onboarding_id', string='Tasks')
    task_count = fields.Integer(string='Total Tasks', compute='_compute_task_stats')
    completed_task_count = fields.Integer(string='Completed Tasks', compute='_compute_task_stats')
    task_progress = fields.Float(string='Task Progress %', compute='_compute_task_stats')
    
    # Documents
    document_ids = fields.One2many('onboarding.document', 'onboarding_id', string='Documents')
    document_count = fields.Integer(string='Total Documents', compute='_compute_document_stats')
    uploaded_document_count = fields.Integer(string='Uploaded Documents', compute='_compute_document_stats')
    verified_document_count = fields.Integer(string='Verified Documents', compute='_compute_document_stats')
    document_progress = fields.Float(string='Document Progress %', compute='_compute_document_stats')
    
    # Employee creation
    employee_id = fields.Many2one('hr.employee', string='Employee Record')
    employee_number = fields.Char(string='Employee Number')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    contract_signed = fields.Boolean(string='Contract Signed', default=False)
    contract_sign_date = fields.Date(string='Contract Sign Date')
    
    # Access
    portal_access_token = fields.Char(string='Portal Access Token', copy=False)
    
    @api.depends('task_ids', 'task_ids.completed')
    def _compute_task_stats(self):
        for record in self:
            total = len(record.task_ids)
            completed = len(record.task_ids.filtered(lambda t: t.completed))
            record.task_count = total
            record.completed_task_count = completed
            record.task_progress = (completed / total * 100) if total > 0 else 0
    
    @api.depends('document_ids', 'document_ids.file', 'document_ids.verified')
    def _compute_document_stats(self):
        for record in self:
            total = len(record.document_ids)
            uploaded = len(record.document_ids.filtered(lambda d: d.file))
            verified = len(record.document_ids.filtered(lambda d: d.verified))
            record.document_count = total
            record.uploaded_document_count = uploaded
            record.verified_document_count = verified
            record.document_progress = (uploaded / total * 100) if total > 0 else 0
    
    @api.model
    def create(self, vals):
        """Create onboarding with default tasks and documents"""
        onboarding = super(HrApplicantOnboarding, self).create(vals)
        onboarding._create_default_tasks()
        onboarding._create_default_documents()
        onboarding._generate_access_token()
        return onboarding
    
    def _create_default_tasks(self):
        """Create default onboarding tasks"""
        self.ensure_one()
        default_tasks = self.env['onboarding.task'].search([('active', '=', True)])
        for task in default_tasks:
            self.env['onboarding.task.line'].create({
                'onboarding_id': self.id,
                'task_id': task.id,
                'name': task.name,
                'description': task.description,
                'sequence': task.sequence,
                'required': task.required,
                'task_type': task.task_type,
            })
    
    def _create_default_documents(self):
        """Create default document requirements"""
        self.ensure_one()
        default_docs = [
            {'name': 'National ID/Passport', 'document_type': 'id', 'sequence': 1, 'required': True},
            {'name': 'Tax PIN Certificate', 'document_type': 'tax_pin', 'sequence': 2, 'required': True},
            {'name': 'NSSF Number', 'document_type': 'nssf', 'sequence': 3, 'required': True},
            {'name': 'NHIF Number', 'document_type': 'nhif', 'sequence': 4, 'required': True},
            {'name': 'Bank Account Details', 'document_type': 'bank_details', 'sequence': 5, 'required': True},
            {'name': 'Academic Certificates', 'document_type': 'certificate', 'sequence': 6, 'required': True},
            {'name': 'Signed Employment Contract', 'document_type': 'contract', 'sequence': 7, 'required': True},
        ]
        for doc in default_docs:
            self.env['onboarding.document'].create({
                'onboarding_id': self.id,
                **doc
            })
    
    def _generate_access_token(self):
        """Generate unique access token for portal"""
        self.ensure_one()
        if not self.portal_access_token:
            import secrets
            self.portal_access_token = secrets.token_urlsafe(32)
    
    def _generate_employee_number(self):
        """Generate employee number"""
        self.ensure_one()
        year = fields.Date.today().year
        sequence = self.env['ir.sequence'].next_by_code('hr.employee.number') or '0001'
        return f"EMP-{year}-{sequence}"
    
    def action_create_employee(self):
        """Create employee record from applicant"""
        self.ensure_one()
        
        if self.employee_id:
            raise UserError(_('Employee record already exists for this applicant.'))
        
        # Check if all required documents are uploaded and verified
        required_docs = self.document_ids.filtered(lambda d: d.required)
        if not all(doc.file and doc.verified for doc in required_docs):
            raise UserError(_('All required documents must be uploaded and verified before creating employee record.'))
        
        # Generate employee number
        employee_number = self._generate_employee_number()
        
        # Create employee
        employee_vals = {
            'name': self.applicant_id.partner_name,
            'job_id': self.applicant_id.job_id.id,
            'department_id': self.applicant_id.department_id.id,
            'company_id': self.applicant_id.company_id.id,
            'work_email': self.applicant_id.email_from,
            'work_phone': self.applicant_id.partner_phone,
            'mobile_phone': self.applicant_id.partner_mobile,
            'employee_type': 'employee',
        }
        
        employee = self.env['hr.employee'].create(employee_vals)
        
        self.write({
            'employee_id': employee.id,
            'employee_number': employee_number,
            'status': 'completed',
            'completion_date': fields.Date.today(),
        })
        
        # Update applicant
        self.applicant_id.write({
            'emp_id': employee.id,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Employee Created'),
                'message': _('Employee record created successfully: %s') % employee_number,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_send_onboarding_invitation(self):
        """Send onboarding portal invitation email"""
        self.ensure_one()
        template = self.env.ref('hr_recruitment_notifications_extended.email_onboarding_welcome', raise_if_not_found=False)
        if template and self.applicant_id.email_from:
            template.send_mail(self.applicant_id.id, force_send=True)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invitation Sent'),
                'message': _('Onboarding invitation sent to %s') % self.applicant_id.email_from,
                'type': 'success',
            }
        }
