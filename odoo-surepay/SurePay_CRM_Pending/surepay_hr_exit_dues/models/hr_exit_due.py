from odoo import models, fields, api

class HrExitDue(models.Model):
    _name = 'hr.exit.due'
    _description = 'HR Exit Due'
    _order = 'employee_id, type, date desc'

    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employee',
        required=True,
        ondelete='cascade'
    )
    
    type = fields.Selection([
        ('salary_balance', 'Salary Balance'),
        ('advance', 'Salary Advance'),
        ('loan', 'Loan Balance'),
        ('other', 'Other Due'),
    ], string='Due Type', required=True, default='other')
    
    description = fields.Char(
        string='Description',
        required=True
    )
    
    amount = fields.Float(
        string='Amount',
        required=True,
        help="Amount due (positive for employee owes company, negative for company owes employee)"
    )
    
    date = fields.Date(
        string='Date',
        default=fields.Date.today,
        required=True
    )
    
    reference = fields.Char(
        string='Reference',
        help="Reference number or document"
    )
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('settled', 'Settled'),
        ('waived', 'Waived'),
    ], string='Status', default='pending', required=True)
    
    settlement_date = fields.Date(
        string='Settlement Date',
        help="Date when this due was settled"
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Department',
        store=True
    )
    
    company_id = fields.Many2one(
        related='employee_id.company_id',
        string='Company',
        store=True
    )
    
    @api.model
    def create(self, vals):
        due = super().create(vals)
        # Update employee exit dues cache
        due.employee_id._compute_total_exit_dues()
        due.employee_id._compute_has_exit_dues()
        return due
    
    def write(self, vals):
        result = super().write(vals)
        # Update employee exit dues cache
        for due in self:
            due.employee_id._compute_total_exit_dues()
            due.employee_id._compute_has_exit_dues()
        return result
    
    def unlink(self):
        employees = self.mapped('employee_id')
        result = super().unlink()
        # Update employee exit dues cache
        for employee in employees:
            employee._compute_total_exit_dues()
            employee._compute_has_exit_dues()
        return result
    
    def action_settle(self):
        """Mark due as settled"""
        self.write({
            'state': 'settled',
            'settlement_date': fields.Date.today()
        })
    
    def action_waive(self):
        """Waive the due"""
        self.write({
            'state': 'waived',
            'settlement_date': fields.Date.today()
        })
    
    def action_reset_pending(self):
        """Reset due to pending status"""
        self.write({
            'state': 'pending',
            'settlement_date': False
        })
