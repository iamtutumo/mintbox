from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'surepay_payroll.hr.loan'
    _description = 'Employee Loan'
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
        help="Date when loan deductions will start from employee's payslip",
        default=fields.Date.today
    )
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('completed', 'Completed')
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
        help="Reason for requesting loan"
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        help="Reason for rejecting the loan"
    )
    
    # Loan-specific fields
    installment_amount = fields.Monetary(
        string='Installment Amount',
        required=True,
        currency_field='currency_id',
        help="Amount to be deducted per payslip"
    )
    
    total_installments = fields.Integer(
        string='Total Installments',
        required=True,
        help="Total number of installments to repay the loan"
    )
    
    installments_paid = fields.Integer(
        string='Installments Paid',
        default=0,
        readonly=True,
        help="Number of installments already paid"
    )
    
    outstanding_balance = fields.Monetary(
        string='Outstanding Balance',
        compute='_compute_outstanding_balance',
        store=True,
        currency_field='currency_id'
    )
    
    remaining_installments = fields.Integer(
        string='Remaining Installments',
        compute='_compute_remaining_installments',
        store=True,
        help="Number of installments remaining to be paid"
    )
    
    # Related fields for payroll integration
    payslip_line_ids = fields.One2many(
        'surepay_payroll.hr.payslip.line', 
        'loan_id', 
        string='Payslip Deductions',
        readonly=True
    )
    
    @api.model
    def _default_employee(self):
        """Get default employee from current user"""
        employee = self.env.user.employee_id
        if not employee:
            raise UserError(_('No employee found for current user. Please contact HR.'))
        return employee.id
    
    @api.depends('amount_requested', 'installment_amount', 'installments_paid', 'payslip_line_ids.total')
    def _compute_outstanding_balance(self):
        """Calculate outstanding balance"""
        for loan in self:
            total_deducted = sum(loan.payslip_line_ids.mapped('total'))
            loan.outstanding_balance = loan.amount_requested - abs(total_deducted)
    
    @api.depends('total_installments', 'installments_paid')
    def _compute_remaining_installments(self):
        """Calculate remaining installments"""
        for loan in self:
            loan.remaining_installments = max(0, loan.total_installments - loan.installments_paid)
    
    @api.constrains('amount_requested')
    def _check_amount_requested(self):
        """Validate requested amount"""
        for loan in self:
            if loan.amount_requested <= 0:
                raise ValidationError(_('Requested amount must be greater than zero.'))
    
    @api.constrains('installment_amount', 'total_installments')
    def _check_installment_plan(self):
        """Validate installment plan"""
        for loan in self:
            if loan.installment_amount <= 0:
                raise ValidationError(_('Installment amount must be greater than zero.'))
            if loan.total_installments <= 0:
                raise ValidationError(_('Total installments must be greater than zero.'))
            if loan.installment_amount * loan.total_installments < loan.amount_requested:
                raise ValidationError(_('Total installment amount must be at least equal to loan amount.'))
    
    def action_submit(self):
        """Submit loan for approval"""
        if self.status != 'draft':
            raise UserError(_('Only draft loans can be submitted.'))
        
        self.write({'status': 'submitted'})
    
    def action_approve(self):
        """Approve loan"""
        if self.status != 'submitted':
            raise UserError(_('Only submitted loans can be approved.'))
        
        self.write({'status': 'approved'})
    
    def action_activate(self):
        """Activate loan (first deduction processed)"""
        if self.status != 'approved':
            raise UserError(_('Only approved loans can be activated.'))
        
        self.write({'status': 'active'})
    
    def action_reject(self):
        """Reject loan"""
        if self.status not in ['submitted', 'approved']:
            raise UserError(_('Only submitted or approved loans can be rejected.'))
        
        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))
        
        self.write({'status': 'rejected'})
    
    def action_complete(self):
        """Mark loan as completed when fully repaid"""
        if self.outstanding_balance > 0:
            raise UserError(_('Cannot complete loan with outstanding balance.'))
        
        self.write({'status': 'completed'})
    
    @api.model
    def process_payroll_deductions(self, payslip):
        """Process loan deductions for a payslip"""
        loans_to_deduct = self.search([
            ('employee_id', '=', payslip.employee_id.id),
            ('status', 'in', ['approved', 'active']),
            ('outstanding_balance', '>', 0)
        ])
        
        deductions = []
        for loan in loans_to_deduct:
            # Calculate deduction amount (minimum of installment amount and outstanding balance)
            deduction_amount = min(loan.installment_amount, loan.outstanding_balance)
            
            if deduction_amount > 0:
                deductions.append({
                    'loan_id': loan.id,
                    'amount': deduction_amount,
                    'name': f'Loan Repayment - {loan.employee_id.name}',
                    'code': 'LOAN'
                })
                
                # Activate loan if first deduction
                if loan.status == 'approved':
                    loan.action_activate()
        
        return deductions
