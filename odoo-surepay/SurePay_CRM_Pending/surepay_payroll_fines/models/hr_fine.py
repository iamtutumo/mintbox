from odoo import models, fields, api

class HrFine(models.Model):
    _name = 'hr.fine'
    _description = 'HR Fine'
    _order = 'date desc, employee_id'

    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employee',
        required=True,
        ondelete='cascade'
    )
    
    fine_rule_id = fields.Many2one(
        'hr.fine.rule',
        string='Fine Rule',
        required=True,
        ondelete='cascade'
    )
    
    date = fields.Date(
        string='Date',
        default=fields.Date.today,
        required=True
    )
    
    amount = fields.Float(
        string='Amount',
        required=True,
        help="Fine amount to be deducted"
    )
    
    description = fields.Text(
        string='Description',
        required=True,
        help="Description of the fine reason"
    )
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('deducted', 'Deducted'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', required=True)
    
    payslip_id = fields.Many2one(
        'surepay_payroll.hr.payslip',
        string='Payslip',
        readonly=True,
        help="Payslip where this fine was deducted"
    )
    
    disciplinary_action_id = fields.Many2one(
        'hr.disciplinary.action',
        string='Disciplinary Action',
        help="Link to disciplinary action if applicable"
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
        fine = super().create(vals)
        return fine
    
    def action_deduct(self):
        """Mark fine as deducted"""
        self.write({'state': 'deducted'})
    
    def action_cancel(self):
        """Cancel the fine"""
        self.write({'state': 'cancelled'})
    
    def action_reset_pending(self):
        """Reset fine to pending status"""
        self.write({'state': 'pending'})
    
    @api.onchange('fine_rule_id')
    def _onchange_fine_rule_id(self):
        """Set amount from fine rule"""
        if self.fine_rule_id:
            self.amount = self.fine_rule_id.default_amount
            if not self.description:
                self.description = self.fine_rule_id.description
