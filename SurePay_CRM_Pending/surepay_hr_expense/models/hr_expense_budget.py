# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar


class HrExpenseBudget(models.Model):
    _name = 'hr.expense.budget'
    _description = 'HR Expense Budget'
    _order = 'employee_id, date_start desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True, readonly=True)
    amount_allocated = fields.Monetary(string='Amount Allocated', currency_field='currency_id', required=True, tracking=True)
    amount_spent = fields.Monetary(string='Amount Spent', currency_field='currency_id', compute='_compute_amount_spent', store=True)
    amount_remaining = fields.Monetary(string='Amount Remaining', currency_field='currency_id', compute='_compute_amount_remaining', store=True)
    budget_utilization = fields.Float(string='Budget Utilization (%)', compute='_compute_budget_utilization', store=True)
    over_budget_amount = fields.Monetary(string='Over Budget Amount', currency_field='currency_id', compute='_compute_over_budget_amount', store=True)
    under_budget_amount = fields.Monetary(string='Under Budget Amount', currency_field='currency_id', compute='_compute_under_budget_amount', store=True)
    period_type = fields.Selection([
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year'),
        ('quarter', 'Quarter'),
        ('custom', 'Custom Range')
    ], string='Period Type', required=True, default='month', tracking=True)
    date_start = fields.Date(string='Start Date', required=True, tracking=True)
    date_end = fields.Date(string='End Date', required=True, tracking=True)
    auto_renew = fields.Boolean(string='Auto Renew', default=True, 
                              help='Automatically create new budget when this period ends')
    rollover_remaining = fields.Boolean(string='Rollover Remaining Amount', default=False,
                                       help='Add remaining amount to next period budget')
    parent_budget_id = fields.Many2one('hr.expense.budget', string='Parent Budget', readonly=True,
                                       help='Parent budget if this is a renewal')
    child_budget_ids = fields.One2many('hr.expense.budget', 'parent_budget_id', string='Child Budgets')
    renewal_count = fields.Integer(string='Renewal Count', default=0, readonly=True,
                                  help='Number of times this budget has been renewed')
    budget_template_id = fields.Many2one('hr.expense.budget.template', string='Budget Template',
                                        help='Template used for automated budget creation')
    is_template = fields.Boolean(string='Is Template', default=False,
                                help='Mark as template for automated budget creation')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, 
                                 default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)
    expense_ids = fields.One2many('hr.expense', 'budget_id', string='Expenses')
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')

    @api.depends('expense_ids', 'expense_ids.state', 'expense_ids.total_amount')
    def _compute_amount_spent(self):
        for budget in self:
            spent_amount = 0.0
            if budget.expense_ids:
                approved_expenses = budget.expense_ids.filtered(
                    lambda exp: exp.state in ['approved', 'done']
                )
                spent_amount = sum(approved_expenses.mapped('total_amount'))
            budget.amount_spent = spent_amount

    @api.depends('amount_allocated', 'amount_spent')
    def _compute_amount_remaining(self):
        for budget in self:
            budget.amount_remaining = budget.amount_allocated - budget.amount_spent

    @api.depends('amount_allocated', 'amount_spent')
    def _compute_budget_utilization(self):
        for budget in self:
            if budget.amount_allocated > 0:
                budget.budget_utilization = (budget.amount_spent / budget.amount_allocated) * 100
            else:
                budget.budget_utilization = 0.0

    @api.depends('amount_allocated', 'amount_spent')
    def _compute_over_budget_amount(self):
        for budget in self:
            if budget.amount_spent > budget.amount_allocated:
                budget.over_budget_amount = budget.amount_spent - budget.amount_allocated
            else:
                budget.over_budget_amount = 0.0

    @api.depends('amount_allocated', 'amount_spent')
    def _compute_under_budget_amount(self):
        for budget in self:
            if budget.amount_spent < budget.amount_allocated:
                budget.under_budget_amount = budget.amount_allocated - budget.amount_spent
            else:
                budget.under_budget_amount = 0.0

    @api.depends('expense_ids')
    def _compute_expense_count(self):
        for budget in self:
            budget.expense_count = len(budget.expense_ids)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for budget in self:
            if budget.date_start > budget.date_end:
                raise ValidationError(_('Start date must be before end date.'))

    @api.constrains('employee_id', 'date_start', 'date_end')
    def _check_overlapping_budgets(self):
        for budget in self:
            overlapping_budgets = self.search([
                ('employee_id', '=', budget.employee_id.id),
                ('id', '!=', budget.id),
                ('state', '!=', 'cancelled'),
                '|',
                '&', ('date_start', '<=', budget.date_start), ('date_end', '>=', budget.date_start),
                '&', ('date_start', '<=', budget.date_end), ('date_end', '>=', budget.date_end),
            ])
            if overlapping_budgets:
                raise ValidationError(_('Budget periods cannot overlap for the same employee.'))

    @api.model
    def _get_period_dates(self, period_type, date=None):
        """Get start and end dates for a given period type"""
        if not date:
            date = fields.Date.today()
        
        if period_type == 'week':
            # ISO week: Monday to Sunday
            start_of_week = date - timedelta(days=date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return start_of_week, end_of_week
        
        elif period_type == 'month':
            # Calendar month
            start_of_month = date.replace(day=1)
            last_day = calendar.monthrange(date.year, date.month)[1]
            end_of_month = date.replace(day=last_day)
            return start_of_month, end_of_month
        
        elif period_type == 'quarter':
            # Calendar quarter
            quarter = (date.month - 1) // 3 + 1
            start_of_quarter = date.replace(month=(quarter - 1) * 3 + 1, day=1)
            end_of_quarter = date.replace(month=quarter * 3, day=1) + timedelta(days=-1)
            return start_of_quarter, end_of_quarter
        
        elif period_type == 'year':
            # Calendar year
            start_of_year = date.replace(month=1, day=1)
            end_of_year = date.replace(month=12, day=31)
            return start_of_year, end_of_year
        
        return None, None
    
    @api.model
    def _get_next_period_dates(self, period_type, current_end_date):
        """Get start and end dates for the next period"""
        next_date = current_end_date + timedelta(days=1)
        return self._get_period_dates(period_type, next_date)
    
    @api.model
    def _get_period_name(self, period_type, date):
        """Get a descriptive name for the period"""
        if period_type == 'week':
            start_of_week = date - timedelta(days=date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return f"Week {date.isocalendar()[1]} {date.year}"
        
        elif period_type == 'month':
            return date.strftime('%B %Y')
        
        elif period_type == 'quarter':
            quarter = (date.month - 1) // 3 + 1
            return f"Q{quarter} {date.year}"
        
        elif period_type == 'year':
            return str(date.year)
        
        return 'Custom Period'

    def action_activate(self):
        """Activate budget and set dates based on period type"""
        for budget in self:
            if budget.period_type != 'custom':
                date_start, date_end = self._get_period_dates(budget.period_type)
                if date_start and date_end:
                    budget.write({
                        'date_start': date_start,
                        'date_end': date_end,
                        'state': 'active'
                    })
                else:
                    raise UserError(_('Cannot determine dates for period type: %s') % budget.period_type)
            else:
                if not budget.date_start or not budget.date_end:
                    raise UserError(_('Custom range requires both start and end dates.'))
                budget.state = 'active'
    
    def create_renewal_budget(self):
        """Create a renewal budget for the next period"""
        self.ensure_one()
        
        if not self.auto_renew:
            raise UserError(_('Budget is not configured for auto-renewal.'))
        
        # Get next period dates
        new_date_start, new_date_end = self._get_next_period_dates(
            self.period_type, self.date_end
        )
        
        if not new_date_start or not new_date_end:
            raise UserError(_('Cannot determine next period dates.'))
        
        # Calculate new allocation amount
        new_allocation = self.amount_allocated
        if self.rollover_remaining and self.amount_remaining > 0:
            new_allocation += self.amount_remaining
        
        # Create new budget
        new_budget = self.create({
            'employee_id': self.employee_id.id,
            'amount_allocated': new_allocation,
            'period_type': self.period_type,
            'date_start': new_date_start,
            'date_end': new_date_end,
            'auto_renew': self.auto_renew,
            'rollover_remaining': self.rollover_remaining,
            'parent_budget_id': self.id,
            'renewal_count': self.renewal_count + 1,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'state': 'active'
        })
        
        # Send notification
        self._send_budget_renewal_notification(new_budget)
        
        return new_budget
    
    def _send_budget_renewal_notification(self, new_budget):
        """Send notification for budget renewal"""
        template = self.env.ref('surepay_hr_expense.mail_template_budget_renewal', raise_if_not_found=False)
        if template:
            template.send_mail(new_budget.id, force_send=True)
    
    def create_budget_from_template(self, employee_id, period_type, date=None):
        """Create budget from template"""
        self.ensure_one()
        
        if not self.is_template:
            raise UserError(_('Budget is not marked as a template.'))
        
        if not date:
            date = fields.Date.today()
        
        date_start, date_end = self._get_period_dates(period_type, date)
        if not date_start or not date_end:
            raise UserError(_('Cannot determine dates for period type: %s') % period_type)
        
        new_budget = self.create({
            'employee_id': employee_id,
            'amount_allocated': self.amount_allocated,
            'period_type': period_type,
            'date_start': date_start,
            'date_end': date_end,
            'auto_renew': self.auto_renew,
            'rollover_remaining': self.rollover_remaining,
            'budget_template_id': self.id,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'state': 'active'
        })
        
        return new_budget

    def action_expire(self):
        """Mark budget as expired"""
        self.write({'state': 'expired'})

    def action_cancel(self):
        """Cancel budget"""
        self.write({'state': 'cancelled'})

    def action_draft(self):
        """Reset budget to draft state"""
        self.write({'state': 'draft'})

    def check_budget_available(self, amount):
        """Check if budget has sufficient amount available"""
        self.ensure_one()
        return self.amount_remaining >= amount

    def get_budget_utilization(self):
        """Get budget utilization percentage"""
        self.ensure_one()
        if self.amount_allocated == 0:
            return 0
        return (self.amount_spent / self.amount_allocated) * 100

    def action_view_expenses(self):
        """View expenses related to this budget"""
        self.ensure_one()
        action = {
            'name': _('Budget Expenses'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense',
            'view_mode': 'tree,form,kanban,pivot,graph',
            'domain': [('budget_id', '=', self.id)],
            'context': {'default_budget_id': self.id}
        }
        return action

    @api.model
    def _cron_check_budget_periods(self):
        """Cron job to check and update budget periods"""
        today = fields.Date.today()
        
        # Expire budgets that have ended
        expired_budgets = self.search([
            ('state', '=', 'active'),
            ('date_end', '<', today)
        ])
        
        for budget in expired_budgets:
            budget.action_expire()
            
            # Create renewal if auto-renew is enabled
            if budget.auto_renew:
                try:
                    budget.create_renewal_budget()
                except Exception as e:
                    # Log error but continue with other budgets
                    self.env['ir.logging'].sudo().create({
                        'name': 'Budget Renewal Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Failed to renew budget {budget.id}: {str(e)}',
                        'dbname': self.env.cr.dbname,
                    })
        
        # Check for upcoming budget expirations (7 days warning)
        upcoming_expiration = today + timedelta(days=7)
        expiring_soon_budgets = self.search([
            ('state', '=', 'active'),
            ('date_end', '=', upcoming_expiration)
        ])
        
        for budget in expiring_soon_budgets:
            budget._send_budget_expiration_warning()
        
        # Auto-create budgets from templates for new employees
        self._auto_create_budgets_for_employees()
        
        # Check budget utilization and send notifications
        self._check_budget_utilization_thresholds()
    
    def _send_budget_expiration_warning(self):
        """Send warning for budget expiration"""
        template = self.env.ref('surepay_hr_expense.mail_template_budget_expiration_warning', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
    
    @api.model
    def _auto_create_budgets_for_employees(self):
        """Automatically create budgets for employees based on templates"""
        templates = self.search([('is_template', '=', True)])
        
        for template in templates:
            # Find employees without active budgets for this template period
            employees_without_budget = self.env['hr.employee'].search([
                ('active', '=', True),
                ('id', 'not in', self.search([
                    ('state', '=', 'active'),
                    ('period_type', '=', template.period_type),
                    ('budget_template_id', '=', template.id)
                ]).mapped('employee_id.id'))
            ])
            
            for employee in employees_without_budget:
                try:
                    template.create_budget_from_template(employee.id, template.period_type)
                except Exception as e:
                    # Log error but continue with other employees
                    self.env['ir.logging'].sudo().create({
                        'name': 'Budget Creation Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Failed to create budget for employee {employee.id} from template {template.id}: {str(e)}',
                        'dbname': self.env.cr.dbname,
                    })
    
    @api.model
    def _check_budget_utilization_thresholds(self):
        """Check budget utilization and send threshold notifications"""
        active_budgets = self.search([('state', '=', 'active')])
        
        for budget in active_budgets:
            utilization = budget.get_budget_utilization()
            
            # 80% utilization warning
            if 80 <= utilization < 100:
                budget._send_utilization_notification('warning')
            
            # 100% utilization alert
            elif utilization >= 100:
                budget._send_utilization_notification('critical')
    
    def _send_utilization_notification(self, threshold_type):
        """Send utilization threshold notification"""
        template_name = 'mail_template_budget_80_percent' if threshold_type == 'warning' else 'mail_template_budget_exceeded'
        template = self.env.ref(f'surepay_hr_expense.{template_name}', raise_if_not_found=False)
        
        if template:
            template.send_mail(self.id, force_send=True)
