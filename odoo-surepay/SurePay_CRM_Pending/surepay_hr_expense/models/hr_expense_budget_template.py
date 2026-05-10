# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrExpenseBudgetTemplate(models.Model):
    _name = 'hr.expense.budget.template'
    _description = 'HR Expense Budget Template'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Template Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    amount_allocated = fields.Monetary(string='Amount Allocated', currency_field='currency_id', required=True, tracking=True)
    period_type = fields.Selection([
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year'),
        ('quarter', 'Quarter'),
        ('custom', 'Custom Range')
    ], string='Period Type', required=True, default='month', tracking=True)
    auto_renew = fields.Boolean(string='Auto Renew', default=True, 
                              help='Automatically create new budget when this period ends')
    rollover_remaining = fields.Boolean(string='Rollover Remaining Amount', default=False,
                                       help='Add remaining amount to next period budget')
    employee_ids = fields.Many2many('hr.employee', string='Employees', 
                                   help='Employees this template applies to. If empty, applies to all employees.')
    department_ids = fields.Many2many('hr.department', string='Departments',
                                     help='Departments this template applies to. If empty, applies to all departments.')
    job_ids = fields.Many2many('hr.job', string='Job Positions',
                              help='Job positions this template applies to. If empty, applies to all job positions.')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, 
                                 default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    budget_ids = fields.One2many('hr.expense.budget', 'budget_template_id', string='Created Budgets', readonly=True)
    budget_count = fields.Integer(string='Budget Count', compute='_compute_budget_count')

    @api.depends('budget_ids')
    def _compute_budget_count(self):
        for template in self:
            template.budget_count = len(template.budget_ids)

    def action_create_budgets(self):
        """Create budgets for applicable employees"""
        self.ensure_one()
        
        # Get applicable employees
        employees = self._get_applicable_employees()
        
        created_budgets = []
        for employee in employees:
            try:
                # Check if employee already has active budget for this period
                existing_budget = self.env['hr.expense.budget'].search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'active'),
                    ('period_type', '=', self.period_type),
                    ('budget_template_id', '=', self.id)
                ])
                
                if not existing_budget:
                    budget = self._create_budget_for_employee(employee)
                    created_budgets.append(budget)
            except Exception as e:
                # Log error but continue with other employees
                self.env['ir.logging'].sudo().create({
                    'name': 'Budget Creation Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f'Failed to create budget for employee {employee.id} from template {self.id}: {str(e)}',
                    'dbname': self.env.cr.dbname,
                })
        
        return {
            'name': _('Created Budgets'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.budget',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [b.id for b in created_budgets])],
            'context': self.env.context
        }

    def _get_applicable_employees(self):
        """Get employees that this template applies to"""
        domain = [('active', '=', True)]
        
        if self.employee_ids:
            domain.append(('id', 'in', self.employee_ids.ids))
        
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        
        if self.job_ids:
            domain.append(('job_id', 'in', self.job_ids.ids))
        
        return self.env['hr.employee'].search(domain)

    def _create_budget_for_employee(self, employee):
        """Create a budget for an employee from this template"""
        budget_model = self.env['hr.expense.budget']
        
        # Get period dates
        date_start, date_end = budget_model._get_period_dates(self.period_type)
        if not date_start or not date_end:
            raise ValidationError(_('Cannot determine dates for period type: %s') % self.period_type)
        
        # Create budget
        budget = budget_model.create({
            'employee_id': employee.id,
            'amount_allocated': self.amount_allocated,
            'period_type': self.period_type,
            'date_start': date_start,
            'date_end': date_end,
            'auto_renew': self.auto_renew,
            'rollover_remaining': self.rollover_remaining,
            'budget_template_id': self.id,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'state': 'active'
        })
        
        return budget

    def action_view_budgets(self):
        """View budgets created from this template"""
        self.ensure_one()
        action = {
            'name': _('Template Budgets'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.budget',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('budget_template_id', '=', self.id)],
            'context': {'default_budget_template_id': self.id}
        }
        return action
