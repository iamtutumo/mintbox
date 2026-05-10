from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrSalaryAdvance(models.Model):
    _name = 'surepay_payroll.hr.salary.advance'
    _description = 'Salary Advance'
    _order = 'date_requested desc'

    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employee', 
        required=True,
        default=lambda self: self._default_employee()
    )
    
    amount_requested = fields.Monetary(
        string='Amount Requested', 
        required=True,
        currency_field='currency_id'
    )
    
    date_requested = fields.Date(
        string='Date Requested', 
        default=fields.Date.today, 
        required=True
    )
    
    deduction_start_date = fields.Date(
        string='Deduction Start Date',
        help="Date when salary advance deduction will start from employee's payslip",
        default=fields.Date.today
    )
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ], string='Status', default='draft', required=True)
    
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        default=lambda self: self.env.company.currency_id
    )
    
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        default=lambda self: self.env.company
    )
    
    reason = fields.Text(
        string='Reason',
        help="Reason for requesting salary advance"
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        help="Reason for rejecting the salary advance"
    )
    
    # Related fields for payroll integration
    payslip_line_ids = fields.One2many(
        'surepay_payroll.hr.payslip.line', 
        'salary_advance_id', 
        string='Payslip Deductions',
        readonly=True
    )
    
    is_deducted = fields.Boolean(
        string='Is Deducted',
        compute='_compute_is_deducted',
        store=True
    )
    
    outstanding_balance = fields.Monetary(
        string='Outstanding Balance',
        compute='_compute_outstanding_balance',
        store=True,
        currency_field='currency_id'
    )
    
    @api.model
    def _default_employee(self):
        """Get default employee from current user"""
        employee = self.env.user.employee_id
        if not employee:
            raise UserError(_('No employee found for current user. Please contact HR.'))
        return employee.id
    
    @api.depends('payslip_line_ids')
    def _compute_is_deducted(self):
        """Check if advance has been deducted from payroll"""
        for advance in self:
            advance.is_deducted = bool(advance.payslip_line_ids)
    
    @api.depends('amount_requested', 'payslip_line_ids.total')
    def _compute_outstanding_balance(self):
        """Compute outstanding balance for salary advance"""
        for advance in self:
            if advance.status in ['approved', 'active'] and not advance.is_deducted:
                advance.outstanding_balance = advance.amount_requested
            else:
                advance.outstanding_balance = 0.0
    
    def action_submit(self):
        """Submit salary advance for approval"""
        if self.status != 'draft':
            raise UserError(_('Only draft advances can be submitted.'))
        
        self.write({'status': 'submitted'})
    
    def action_approve(self):
        """Approve salary advance"""
        if self.status != 'submitted':
            raise UserError(_('Only submitted advances can be approved.'))
        
        self.write({'status': 'approved'})
    
    def action_reject(self):
        """Reject salary advance"""
        if self.status not in ['submitted', 'approved']:
            raise UserError(_('Only submitted or approved advances can be rejected.'))
        
        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))
        
        self.write({'status': 'rejected'})
    
    def action_mark_paid(self):
        """Mark advance as paid (after payroll deduction)"""
        if self.status != 'approved':
            raise UserError(_('Only approved advances can be marked as paid.'))
        
        if not self.is_deducted:
            raise UserError(_('Advance must be deducted from payroll before marking as paid.'))
        
        self.write({'status': 'paid'})
    
    @api.model
    def process_payroll_deductions(self, payslip):
        """Process salary advance deductions for a payslip"""
        advances_to_deduct = self.search([
            ('employee_id', '=', payslip.employee_id.id),
            ('status', '=', 'approved'),
            ('is_deducted', '=', False)
        ])
        
        deductions = []
        for advance in advances_to_deduct:
            deductions.append({
                'salary_advance_id': advance.id,
                'amount': advance.amount_requested,
                'name': f'Salary Advance Deduction - {advance.employee_id.name}',
                'code': 'ADVANCE'
            })
        
        return deductions
