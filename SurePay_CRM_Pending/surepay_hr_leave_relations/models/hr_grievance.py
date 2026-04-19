from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, timedelta


class HrGrievance(models.Model):
    _name = 'hr.grievance'
    _description = 'HR Grievance'
    _order = 'submission_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                   store=True, readonly=True)
    
    manager_id = fields.Many2one('hr.employee', string='Department Manager', related='employee_id.parent_id',
                                 store=True, readonly=True)
    
    hr_manager_id = fields.Many2one('hr.employee', string='HR Manager', compute='_compute_hr_manager',
                                   store=True, readonly=True)
    
    grievance_type = fields.Selection([
        ('workplace_harassment', 'Workplace Harassment'),
        ('discrimination', 'Discrimination'),
        ('unfair_treatment', 'Unfair Treatment'),
        ('working_conditions', 'Working Conditions'),
        ('compensation', 'Compensation'),
        ('termination', 'Termination'),
        ('policy_violation', 'Policy Violation'),
        ('interpersonal_conflict', 'Interpersonal Conflict'),
        ('performance_related', 'Performance Related'),
        ('safety_concern', 'Safety Concern'),
        ('other', 'Other')
    ], string='Grievance Type', required=True)
    
    title = fields.Char(string='Title', required=True)
    
    description = fields.Text(string='Description', required=True)
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('manager_review', 'Manager Review'),
        ('hr_review', 'HR Review'),
        ('under_investigation', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('closed', 'Closed')
    ], string='Status', default='draft', required=True)
    
    submission_date = fields.Date(string='Submission Date', required=True,
                                 default=fields.Date.today(),
                                 readonly=True)
    
    assigned_to = fields.Many2one('hr.employee', string='Assigned To',
                                 domain="[('department_id', '=', department_id), ('id', '!=', employee_id)]")
    
    investigation_officer_id = fields.Many2one('hr.employee', string='Investigation Officer',
                                             readonly=True,
                                             domain="[('department_id.name', '=', 'Human Resources'), ('id', '!=', employee_id)]")
    
    investigation_start_date = fields.Date(string='Investigation Start Date',
                                         readonly=True)
    
    investigation_end_date = fields.Date(string='Investigation End Date',
                                       readonly=True)
    
    investigation_report = fields.Text(string='Investigation Report',
                                     readonly=True)
    
    action_taken = fields.Text(string='Action Taken', readonly=True)
    
    follow_up_date = fields.Date(string='Follow Up Date', readonly=True)
    
    satisfaction_rating = fields.Selection([
        ('very_satisfied', 'Very Satisfied'),
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('dissatisfied', 'Dissatisfied'),
        ('very_dissatisfied', 'Very Dissatisfied')
    ], string='Satisfaction Rating', readonly=True)
    
    is_confidential = fields.Boolean(string='Confidential', default=False)
    
    witness_ids = fields.Many2many('hr.employee', string='Witnesses',
                                  domain="[('id', '!=', employee_id)]")
    
    related_incident_ids = fields.Many2many('hr.grievance', 'grievance_incident_rel',
                                          'grievance_id', 'related_grievance_id',
                                          string='Related Incidents')
    
    resolution_notes = fields.Text(string='Resolution Notes',
                                  readonly=True)
    
    escalation_date = fields.Date(string='Escalation Date')
    
    days_open = fields.Integer(string='Days Open', compute='_compute_days_open',
                              store=True)
    
    disciplinary_action_ids = fields.Many2many('hr.disciplinary.action',
                                              string='Related Disciplinary Actions',
                                              readonly=True)
    
    disciplinary_action_count = fields.Integer(string='Disciplinary Actions Count',
                                               compute='_compute_disciplinary_action_count')
    
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium', required=True,
       readonly=True)
    
    expected_resolution_date = fields.Date(string='Expected Resolution Date')
    
    @api.depends('department_id')
    def _compute_hr_manager(self):
        for grievance in self:
            if grievance.department_id:
                # Find HR manager from HR department
                hr_department = self.env['hr.department'].search([('name', '=', 'Human Resources')], limit=1)
                if hr_department:
                    hr_manager = self.env['hr.employee'].search([
                        ('department_id', '=', hr_department.id),
                        ('parent_id', '=', False)  # Top-level HR employee
                    ], limit=1)
                    grievance.hr_manager_id = hr_manager.id if hr_manager else False
                else:
                    grievance.hr_manager_id = False
            else:
                grievance.hr_manager_id = False
    
    @api.depends('submission_date', 'status')
    def _compute_days_open(self):
        today = fields.Date.today()
        for grievance in self:
            if grievance.submission_date and grievance.status not in ['resolved', 'closed']:
                grievance.days_open = (today - grievance.submission_date).days
            else:
                grievance.days_open = 0
    
    @api.depends('disciplinary_action_ids')
    def _compute_disciplinary_action_count(self):
        for grievance in self:
            grievance.disciplinary_action_count = len(grievance.disciplinary_action_ids)
    
    @api.model
    def _check_escalation_deadline(self):
        """Check for grievances that need escalation"""
        escalation_threshold = 7  # 7 days for escalation
        today = fields.Date.today()
        
        grievances_to_escalate = self.search([
            ('status', 'in', ['manager_review', 'hr_review', 'under_investigation']),
            ('submission_date', '<=', today - timedelta(days=escalation_threshold)),
            ('escalation_date', '=', False)
        ])
        
        for grievance in grievances_to_escalate:
            grievance.action_escalate()
    
    def action_submit(self):
        self.write({'status': 'submitted'})
        self._notify_hr_officer()
        # Auto-assign to department manager if available
        for grievance in self:
            if grievance.manager_id and not grievance.assigned_to:
                grievance.write({'assigned_to': grievance.manager_id.id})
                grievance.action_manager_review()
    
    def action_assign(self):
        """Assign grievance and start review process"""
        if not self.assigned_to:
            raise ValidationError(_('Please assign the grievance to someone before proceeding.'))
        self.action_manager_review()
    
    def action_manager_review(self):
        self.write({'status': 'manager_review'})
        self._notify_manager()
    
    def action_hr_review(self):
        self.write({'status': 'hr_review'})
        self._notify_hr_manager()
    
    def action_start_investigation(self):
        self.write({
            'status': 'under_investigation',
            'investigation_start_date': fields.Date.today()
        })
        self._notify_investigation_officer()
    
    def action_complete_investigation(self):
        self.write({'investigation_end_date': fields.Date.today()})
        self._notify_investigation_complete()
    
    def action_resolve(self):
        self.write({'status': 'resolved'})
        self._notify_employee_resolution()
    
    def action_escalate(self):
        self.write({
            'status': 'escalated',
            'escalation_date': fields.Date.today()
        })
        self._notify_hr_manager()
    
    def action_close(self):
        self.write({'status': 'closed'})
    
    def action_reject(self):
        self.write({'status': 'closed'})
        self._notify_employee_rejection()
    
    def action_reset_draft(self):
        self.write({'status': 'draft'})
    
    def action_view_disciplinary_actions(self):
        """View related disciplinary actions"""
        self.ensure_one()
        action = {
            'name': _('Disciplinary Actions'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.disciplinary.action',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.disciplinary_action_ids.ids)],
            'context': {'default_employee_id': self.employee_id.id},
        }
        if len(self.disciplinary_action_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.disciplinary_action_ids.id,
            })
        return action
    
    def _notify_hr_officer(self):
        """Notify HR Officer about new grievance"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_grievance_submitted')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _notify_manager(self):
        """Notify department manager about grievance assignment"""
        if self.assigned_to and self.assigned_to.work_email:
            template = self.env.ref('surepay_hr_leave_relations.email_template_grievance_assigned')
            if template:
                template.send_mail(self.id, force_send=True)
    
    def _notify_hr_manager(self):
        """Notify HR Manager about escalated grievance"""
        if self.hr_manager_id and self.hr_manager_id.work_email:
            template = self.env.ref('surepay_hr_leave_relations.email_template_grievance_escalated')
            if template:
                template.send_mail(self.id, force_send=True)
    
    def _notify_investigation_officer(self):
        """Notify investigation officer about investigation assignment"""
        if self.investigation_officer_id and self.investigation_officer_id.work_email:
            template = self.env.ref('surepay_hr_leave_relations.email_template_grievance_investigation')
            if template:
                template.send_mail(self.id, force_send=True)
    
    def _notify_investigation_complete(self):
        """Notify stakeholders about investigation completion"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_grievance_investigation_complete')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _notify_employee_resolution(self):
        """Notify employee about grievance resolution"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_grievance_resolved')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _notify_employee_rejection(self):
        """Notify employee about grievance rejection"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_grievance_rejected')
        if template:
            template.send_mail(self.id, force_send=True)
    
    @api.constrains('expected_resolution_date')
    def _check_expected_resolution_date(self):
        for grievance in self:
            if grievance.expected_resolution_date and grievance.expected_resolution_date < grievance.submission_date:
                raise ValidationError(_('Expected resolution date must be after submission date.'))
    
    @api.model_create_multi
    def create(self, vals_list):
        grievances = super(HrGrievance, self).create(vals_list)
        # Auto-assign to department manager if available
        for grievance in grievances:
            if grievance.manager_id and not grievance.assigned_to:
                grievance.write({'assigned_to': grievance.manager_id.id})
        return grievances
    
    def write(self, vals):
        result = super(HrGrievance, self).write(vals)
        # Check if assigned_to is updated and status is submitted
        if 'assigned_to' in vals and vals.get('assigned_to'):
            for grievance in self:
                if grievance.status == 'submitted':
                    grievance.action_manager_review()
        return result
    
    def _valid_field_parameter(self, field, name):
        """Override to handle deprecated tracking parameter"""
        if name == 'tracking':
            return True  # Accept but ignore the tracking parameter
        return super()._valid_field_parameter(field, name)
