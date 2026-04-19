# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    expense_budget_ids = fields.One2many('hr.expense.budget', 'employee_id', string='Expense Budgets')
    current_budget_id = fields.Many2one('hr.expense.budget', string='Current Budget', 
                                       compute='_compute_current_budget', store=True)
    total_budget_allocated = fields.Monetary(string='Total Budget Allocated', 
                                           currency_field='currency_id',
                                           compute='_compute_budget_totals', store=True)
    total_budget_spent = fields.Monetary(string='Total Budget Spent', 
                                        currency_field='currency_id',
                                        compute='_compute_budget_totals', store=True)
    total_budget_remaining = fields.Monetary(string='Total Budget Remaining', 
                                           currency_field='currency_id',
                                           compute='_compute_budget_totals', store=True)
    budget_utilization = fields.Float(string='Budget Utilization %', 
                                     compute='_compute_budget_utilization', store=True)
    current_budget_amount_allocated = fields.Monetary(string='Current Budget Allocated', 
                                                     currency_field='currency_id',
                                                     related='current_budget_id.amount_allocated', readonly=True)
    current_budget_amount_remaining = fields.Monetary(string='Current Budget Remaining', 
                                                     currency_field='currency_id',
                                                     related='current_budget_id.amount_remaining', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                 related='company_id.currency_id', readonly=True)

    @api.depends('expense_budget_ids', 'expense_budget_ids.state', 'expense_budget_ids.date_start', 
                 'expense_budget_ids.date_end')
    def _compute_current_budget(self):
        today = fields.Date.today()
        for employee in self:
            current_budget = self.env['hr.expense.budget'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'active'),
                ('date_start', '<=', today),
                ('date_end', '>=', today)
            ], limit=1)
            employee.current_budget_id = current_budget

    @api.depends('expense_budget_ids', 'expense_budget_ids.amount_allocated', 
                 'expense_budget_ids.amount_spent', 'expense_budget_ids.state')
    def _compute_budget_totals(self):
        for employee in self:
            active_budgets = employee.expense_budget_ids.filtered(
                lambda b: b.state in ['active', 'expired']
            )
            employee.total_budget_allocated = sum(active_budgets.mapped('amount_allocated'))
            employee.total_budget_spent = sum(active_budgets.mapped('amount_spent'))
            employee.total_budget_remaining = sum(active_budgets.mapped('amount_remaining'))

    @api.depends('total_budget_allocated', 'total_budget_spent')
    def _compute_budget_utilization(self):
        for employee in self:
            if employee.total_budget_allocated and employee.total_budget_allocated > 0:
                employee.budget_utilization = (employee.total_budget_spent / employee.total_budget_allocated) * 100
            else:
                employee.budget_utilization = 0.0

    def action_view_budgets(self):
        """View all budgets for this employee"""
        self.ensure_one()
        action = {
            'name': _('Employee Budgets'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.budget',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'search_default_group_by_state': 1,
                'search_default_group_by_period_type': 1
            }
        }
        return action

    def action_create_budget(self):
        """Create a new budget for this employee"""
        self.ensure_one()
        action = {
            'name': _('Create Budget'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.budget',
            'view_mode': 'form',
            'context': {
                'default_employee_id': self.id,
                'default_currency_id': self.currency_id.id,
                'default_company_id': self.company_id.id
            }
        }
        return action

    def get_current_budget_status(self):
        """Get current budget status for the employee"""
        self.ensure_one()
        if not self.current_budget_id:
            return {
                'has_budget': False,
                'message': _('No active budget found for current period.')
            }
        
        budget = self.current_budget_id
        utilization = budget.get_budget_utilization()
        
        return {
            'has_budget': True,
            'budget_id': budget.id,
            'allocated': budget.amount_allocated,
            'spent': budget.amount_spent,
            'remaining': budget.amount_remaining,
            'utilization_percent': utilization,
            'period_type': budget.period_type,
            'date_start': budget.date_start,
            'date_end': budget.date_end,
            'state': budget.state
        }

    def check_expense_budget_availability(self, amount):
        """Check if employee has sufficient budget for an expense"""
        self.ensure_one()
        if not self.current_budget_id:
            return {
                'available': False,
                'message': _('No active budget found for current period.')
            }
        
        budget = self.current_budget_id
        if budget.state != 'active':
            return {
                'available': False,
                'message': _('Current budget is not active.')
            }
        
        if budget.check_budget_available(amount):
            return {
                'available': True,
                'budget_id': budget.id,
                'remaining_after_expense': budget.amount_remaining - amount
            }
        else:
            return {
                'available': False,
                'budget_id': budget.id,
                'shortage': amount - budget.amount_remaining,
                'message': _('Insufficient budget. Required: %s, Available: %s') % (
                    amount, budget.amount_remaining
                )
            }
