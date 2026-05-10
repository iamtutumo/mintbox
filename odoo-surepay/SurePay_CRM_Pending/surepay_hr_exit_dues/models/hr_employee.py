from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    exit_due_ids = fields.One2many(
        'hr.exit.due', 'employee_id', 
        string='Exit Dues',
        help="Exit dues and settlements for this employee"
    )
    
    total_exit_dues = fields.Float(
        string='Total Exit Dues',
        compute='_compute_total_exit_dues',
        store=True,
        help="Total amount of exit dues"
    )
    
    has_exit_dues = fields.Boolean(
        string='Has Exit Dues',
        compute='_compute_has_exit_dues',
        store=True,
        help="Whether employee has pending exit dues"
    )
    
    @api.depends('exit_due_ids.amount')
    def _compute_total_exit_dues(self):
        for employee in self:
            employee.total_exit_dues = sum(employee.exit_due_ids.mapped('amount'))
    
    @api.depends('exit_due_ids')
    def _compute_has_exit_dues(self):
        for employee in self:
            employee.has_exit_dues = bool(employee.exit_due_ids)
    
    def action_calculate_exit_dues(self):
        """Calculate exit dues for the employee"""
        self.ensure_one()
        
        # Clear existing exit dues
        self.exit_due_ids.unlink()
        
        # Calculate salary balance (pro-rated for current month)
        salary_balance = self._calculate_salary_balance()
        if salary_balance > 0:
            self.env['hr.exit.due'].create({
                'employee_id': self.id,
                'type': 'salary_balance',
                'description': 'Salary Balance',
                'amount': salary_balance,
            })
        
        # Get outstanding advances
        advances = self._get_outstanding_advances()
        for advance in advances:
            self.env['hr.exit.due'].create({
                'employee_id': self.id,
                'type': 'advance',
                'description': advance['description'],
                'amount': advance['amount'],
                'reference': advance.get('reference'),
            })
        
        # Get outstanding loans
        loans = self._get_outstanding_loans()
        for loan in loans:
            self.env['hr.exit.due'].create({
                'employee_id': self.id,
                'type': 'loan',
                'description': loan['description'],
                'amount': loan['amount'],
                'reference': loan.get('reference'),
            })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exit Dues',
            'res_model': 'hr.employee',
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }
    
    def _calculate_salary_balance(self):
        """Calculate pro-rated salary balance for current month"""
        self.ensure_one()
        contract = self.contract_id
        if not contract or not contract.wage:
            return 0.0
        
        today = fields.Date.today()
        month_start = today.replace(day=1)
        month_end = (month_start + fields.timedelta(days=32)).replace(day=1) - fields.timedelta(days=1)
        
        # Calculate worked days in current month
        worked_days = (today - month_start).days + 1
        total_days = (month_end - month_start).days + 1
        
        # Pro-rated salary
        daily_rate = contract.wage / total_days
        return daily_rate * worked_days
    
    def _get_outstanding_advances(self):
        """Get outstanding salary advances"""
        self.ensure_one()
        advances = []
        
        # Look for advance models (this may need adjustment based on your setup)
        advance_model = self.env['hr.salary.advance']
        if hasattr(advance_model, 'search'):
            outstanding_advances = advance_model.search([
                ('employee_id', '=', self.id),
                ('state', '=', 'approved'),
                ('paid', '=', False),
            ])
            for advance in outstanding_advances:
                advances.append({
                    'description': f'Salary Advance - {advance.date}',
                    'amount': advance.amount,
                    'reference': advance.name,
                })
        
        return advances
    
    def _get_outstanding_loans(self):
        """Get outstanding loans"""
        self.ensure_one()
        loans = []
        
        # Look for loan models (this may need adjustment based on your setup)
        loan_model = self.env['hr.loan']
        if hasattr(loan_model, 'search'):
            outstanding_loans = loan_model.search([
                ('employee_id', '=', self.id),
                ('state', '=', 'approved'),
                ('balance_amount', '>', 0),
            ])
            for loan in outstanding_loans:
                loans.append({
                    'description': f'Loan Balance - {loan.name}',
                    'amount': loan.balance_amount,
                    'reference': loan.name,
                })
        
        return loans
