# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    budget_id = fields.Many2one('hr.expense.budget', string='Budget', 
                               tracking=True, readonly=True)
    approval_level = fields.Selection([
        ('standard', 'Standard Approval'),
        ('override_required', 'Override Approval Required'),
        ('escalated', 'Escalated to Senior Management'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Approval Level', default='standard', tracking=True)
    
    override_requested_by = fields.Many2one('res.users', string='Override Requested By', readonly=True)
    override_requested_date = fields.Datetime(string='Override Request Date', readonly=True)
    override_approved_by = fields.Many2one('res.users', string='Override Approved By', readonly=True)
    override_approved_date = fields.Datetime(string='Override Approval Date', readonly=True)
    override_notes = fields.Text(string='Override Notes')
    
    escalation_requested_by = fields.Many2one('res.users', string='Escalation Requested By', readonly=True)
    escalation_requested_date = fields.Datetime(string='Escalation Request Date', readonly=True)
    escalation_approved_by = fields.Many2one('res.users', string='Escalation Approved By', readonly=True)
    escalation_approved_date = fields.Datetime(string='Escalation Approval Date', readonly=True)
    escalation_notes = fields.Text(string='Escalation Notes')
    
    budget_check_result = fields.Text(string='Budget Check Result', readonly=True)
    requires_override_approval = fields.Boolean(string='Requires Override Approval', 
                                               compute='_compute_requires_override_approval', 
                                               store=True)
    budget_utilization_at_submission = fields.Float(string='Budget Utilization at Submission (%)',
                                                   compute='_compute_budget_utilization_at_submission',
                                                   store=True)
    
    # Related fields for budget amounts to avoid dotted notation in views
    budget_amount_allocated = fields.Monetary(related='budget_id.amount_allocated', 
                                            string='Budget Allocated', readonly=True)
    budget_amount_spent = fields.Monetary(related='budget_id.amount_spent', 
                                        string='Budget Spent', readonly=True)
    budget_amount_remaining = fields.Monetary(related='budget_id.amount_remaining', 
                                           string='Budget Remaining', readonly=True)
    budget_display_name = fields.Char(related='budget_id.display_name', 
                                    string='Budget Name', readonly=True)

    @api.depends('budget_id', 'total_amount', 'budget_id.amount_allocated', 'budget_id.amount_spent')
    def _compute_requires_override_approval(self):
        for expense in self:
            if expense.budget_id and expense.total_amount:
                # Check if expense exceeds available budget
                available_budget = expense.budget_id.amount_remaining
                expense.requires_override_approval = expense.total_amount > available_budget
            else:
                expense.requires_override_approval = False

    @api.depends('budget_id', 'total_amount', 'budget_id.amount_allocated', 'budget_id.amount_spent')
    def _compute_budget_utilization_at_submission(self):
        for expense in self:
            if expense.budget_id:
                utilization = expense.budget_id.get_budget_utilization()
                expense.budget_utilization_at_submission = utilization
            else:
                expense.budget_utilization_at_submission = 0

    @api.model
    def default_get(self, fields):
        res = super(HrExpense, self).default_get(fields)
        
        # Set default budget if employee has active budget
        if 'employee_id' in res and res.get('employee_id'):
            employee = self.env['hr.employee'].browse(res['employee_id'])
            if employee.current_budget_id:
                res['budget_id'] = employee.current_budget_id.id
        
        # If current user is employee, set their employee_id
        if not res.get('employee_id'):
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            if employee:
                res['employee_id'] = employee.id
                if employee.current_budget_id:
                    res['budget_id'] = employee.current_budget_id.id
        
        return res

    @api.constrains('budget_id', 'date')
    def _check_budget_period(self):
        for expense in self:
            if expense.budget_id:
                if expense.date < expense.budget_id.date_start or expense.date > expense.budget_id.date_end:
                    raise ValidationError(_('Expense date must be within the budget period (%s to %s).') % (
                        expense.budget_id.date_start, expense.budget_id.date_end
                    ))

    def action_submit_expenses(self):
        """Override submit action to include budget validation"""
        for expense in self:
            if not expense.budget_id:
                raise UserError(_('Please select a budget for this expense.'))
            
            # Validate budget is active
            if expense.budget_id.state != 'active':
                raise UserError(_('The selected budget is not active. Please select an active budget.'))
            
            # Check budget availability
            budget_check = expense.employee_id.check_expense_budget_availability(expense.total_amount)
            expense.budget_check_result = budget_check.get('message', '')
            
            if not budget_check['available']:
                # Budget exceeded, requires override approval
                expense.requires_override_approval = True
                expense.approval_level = 'override_required'
            else:
                expense.requires_override_approval = False
                expense.approval_level = 'standard'
        
        return super(HrExpense, self).action_submit_expenses()

    def approve_expense_sheets(self):
        """Override approval to check budget constraints"""
        for expense in self:
            if expense.requires_override_approval:
                # Check if user has override rights
                if not self.user_has_override_rights():
                    raise UserError(_('You do not have permission to approve expenses that exceed the budget.'))
                
                # Process override approval
                expense._process_override_approval()
                
                # Send notification to HR/Finance
                self._send_override_approval_notification(expense)
            else:
                # Standard approval
                expense.approval_level = 'approved'
                expense.write({
                    'override_approved_by': self.env.user.id,
                    'override_approved_date': fields.Datetime.now()
                })
        
        return super(HrExpense, self).approve_expense_sheets()

    def user_has_override_rights(self):
        """Check if current user has rights to approve over-budget expenses"""
        return self.user_has_groups('account.group_account_manager') or \
               self.user_has_groups('hr.group_hr_manager')

    def _send_override_approval_notification(self, expense):
        """Send notification for override approval"""
        template = self.env.ref('surepay_hr_expense.mail_template_budget_override', raise_if_not_found=False)
        if template:
            template.send_mail(expense.id, force_send=True)

    def write(self, vals):
        """Override write to update budget when expense is approved"""
        result = super(HrExpense, self).write(vals)
        
        # Check if state changed to approved or done
        if 'state' in vals and vals['state'] in ['approved', 'done']:
            for expense in self:
                if expense.budget_id:
                    # Trigger budget recomputation
                    expense.budget_id._compute_amount_spent()
                    expense.budget_id._compute_amount_remaining()
                    
                    # Check for budget threshold notifications
                    self._check_budget_threshold_notifications(expense)
        
        return result

    def _check_budget_threshold_notifications(self, expense):
        """Check and send budget threshold notifications"""
        if not expense.budget_id:
            return
        
        budget = expense.budget_id
        utilization = budget.get_budget_utilization()
        
        # 80% threshold notification
        if 80 <= utilization < 100:
            self._send_budget_threshold_notification(budget, 'warning')
        
        # 100% threshold notification (exceeded)
        elif utilization >= 100:
            self._send_budget_threshold_notification(budget, 'critical')

    def _send_budget_threshold_notification(self, budget, threshold_type):
        """Send budget threshold notification"""
        template_name = 'mail_template_budget_80_percent' if threshold_type == 'warning' else 'mail_template_budget_exceeded'
        template = self.env.ref(f'surepay_hr_expense.{template_name}', raise_if_not_found=False)
        
        if template:
            # Send to employee and manager
            recipients = [budget.employee_id.work_email]
            if budget.employee_id.parent_id and budget.employee_id.parent_id.work_email:
                recipients.append(budget.employee_id.parent_id.work_email)
            
            # For critical threshold, also notify HR and Finance
            if threshold_type == 'critical':
                hr_users = self.env['res.users'].search([
                    ('groups_id', 'in', [
                        self.env.ref('hr.group_hr_manager').id,
                        self.env.ref('account.group_account_manager').id
                    ])
                ])
                for user in hr_users:
                    if user.email:
                        recipients.append(user.email)
            
            # Remove duplicates and send
            recipients = list(set(recipients))
            for recipient in recipients:
                if recipient:
                    template.with_context(email_to=recipient).send_mail(budget.id, force_send=True)

    @api.model
    def _get_budget_for_expense(self, employee_id, date):
        """Get the appropriate budget for an expense based on date"""
        return self.env['hr.expense.budget'].search([
            ('employee_id', '=', employee_id),
            ('state', '=', 'active'),
            ('date_start', '<=', date),
            ('date_end', '>=', date)
        ], limit=1)

    def unlink(self):
        """Override unlink to update budget when expense is deleted"""
        budget_ids = self.mapped('budget_id').ids
        result = super(HrExpense, self).unlink()
        
        # Update budget computations
        if budget_ids:
            budgets = self.env['hr.expense.budget'].browse(budget_ids)
            budgets._compute_amount_spent()
            budgets._compute_amount_remaining()
        
        return result

    def _process_override_approval(self):
        """Process override approval with escalation logic"""
        self.ensure_one()
        
        # Check if escalation is needed (e.g., over 150% of budget)
        if self.budget_id and self.total_amount > (self.budget_id.amount_allocated * 1.5):
            # Requires escalation to senior management
            self.approval_level = 'escalated'
            self._request_escalation()
            return
        
        # Standard override approval
        self.approval_level = 'approved'
        self.write({
            'override_approved_by': self.env.user.id,
            'override_approved_date': fields.Datetime.now()
        })
    
    def _request_escalation(self):
        """Request escalation to senior management"""
        self.ensure_one()
        
        self.write({
            'escalation_requested_by': self.env.user.id,
            'escalation_requested_date': fields.Datetime.now()
        })
        
        # Send escalation notification
        template = self.env.ref('surepay_hr_expense.mail_template_budget_escalation', raise_if_not_found=False)
        if template:
            # Get senior management users
            senior_users = self.env['res.users'].search([
                ('groups_id', 'in', [
                    self.env.ref('base.group_system').id,
                    self.env.ref('account.group_account_manager').id
                ])
            ])
            
            for user in senior_users:
                if user.email:
                    template.with_context(email_to=user.email).send_mail(self.id, force_send=True)
    
    def action_approve_escalation(self):
        """Approve escalated expense"""
        self.ensure_one()
        
        if not self.user_has_escalation_rights():
            raise UserError(_('You do not have permission to approve escalated expenses.'))
        
        self.write({
            'approval_level': 'approved',
            'escalation_approved_by': self.env.user.id,
            'escalation_approved_date': fields.Datetime.now()
        })
        
        # Send approval notification
        self._send_escalation_approval_notification()
    
    def action_reject_escalation(self):
        """Reject escalated expense"""
        self.ensure_one()
        
        if not self.user_has_escalation_rights():
            raise UserError(_('You do not have permission to reject escalated expenses.'))
        
        self.write({
            'approval_level': 'rejected',
            'escalation_approved_by': self.env.user.id,
            'escalation_approved_date': fields.Datetime.now()
        })
        
        # Send rejection notification
        self._send_escalation_rejection_notification()
        
        # Reset expense to draft
        self.write({'state': 'draft'})
    
    def user_has_escalation_rights(self):
        """Check if current user has rights to approve escalated expenses"""
        return self.user_has_groups('base.group_system') or \
               self.user_has_groups('account.group_account_manager')
    
    def _send_escalation_approval_notification(self):
        """Send escalation approval notification"""
        template = self.env.ref('surepay_hr_expense.mail_template_escalation_approved', raise_if_not_found=False)
        if template:
            # Notify employee, manager, and original approver
            recipients = [self.employee_id.work_email]
            if self.employee_id.parent_id and self.employee_id.parent_id.work_email:
                recipients.append(self.employee_id.parent_id.work_email)
            if self.override_approved_by and self.override_approved_by.email:
                recipients.append(self.override_approved_by.email)
            
            recipients = list(set(recipients))
            for recipient in recipients:
                if recipient:
                    template.with_context(email_to=recipient).send_mail(self.id, force_send=True)
    
    def _send_escalation_rejection_notification(self):
        """Send escalation rejection notification"""
        template = self.env.ref('surepay_hr_expense.mail_template_escalation_rejected', raise_if_not_found=False)
        if template:
            # Notify employee, manager, and original approver
            recipients = [self.employee_id.work_email]
            if self.employee_id.parent_id and self.employee_id.parent_id.work_email:
                recipients.append(self.employee_id.parent_id.work_email)
            if self.override_approved_by and self.override_approved_by.email:
                recipients.append(self.override_approved_by.email)
            
            recipients = list(set(recipients))
            for recipient in recipients:
                if recipient:
                    template.with_context(email_to=recipient).send_mail(self.id, force_send=True)
    
    def action_view_budget(self):
        """View the budget associated with this expense"""
        self.ensure_one()
        if self.budget_id:
            return {
                'name': _('Budget'),
                'type': 'ir.actions.act_window',
                'res_model': 'hr.expense.budget',
                'res_id': self.budget_id.id,
                'view_mode': 'form',
            }
        else:
            raise UserError(_('No budget associated with this expense.'))

    def get_budget_summary(self):
        """Get budget summary for the expense"""
        self.ensure_one()
        if not self.budget_id:
            return {
                'has_budget': False,
                'message': _('No budget associated with this expense.')
            }
        
        budget = self.budget_id
        return {
            'has_budget': True,
            'budget_id': budget.id,
            'allocated': budget.amount_allocated,
            'spent': budget.amount_spent,
            'remaining': budget.amount_remaining,
            'utilization_percent': budget.get_budget_utilization(),
            'period_type': budget.period_type,
            'date_start': budget.date_start,
            'date_end': budget.date_end,
            'state': budget.state
        }
