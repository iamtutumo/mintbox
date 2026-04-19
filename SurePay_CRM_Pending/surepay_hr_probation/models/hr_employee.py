from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_probation = fields.Boolean(
        string='On Probation',
        default=False,
        help="Check if the employee is currently on probation",
        tracking=True
    )
    
    probation_start_date = fields.Date(
        string='Probation Start Date',
        help="Date when probation period started",
        tracking=True
    )
    
    probation_end_date = fields.Date(
        string='Probation End Date',
        help="Date when probation period ends",
        tracking=True
    )
    
    @api.depends('is_probation', 'probation_end_date')
    def _compute_probation_status(self):
        today = fields.Date.today()
        for employee in self:
            if employee.is_probation:
                if employee.probation_end_date and employee.probation_end_date < today:
                    employee.probation_status = 'expired'
                else:
                    employee.probation_status = 'active'
            else:
                employee.probation_status = 'none'
    
    probation_status = fields.Selection([
        ('none', 'Not on Probation'),
        ('active', 'On Probation'),
        ('expired', 'Probation Expired'),
    ], string='Probation Status', compute='_compute_probation_status', store=True)
    
    def toggle_probation(self):
        """Toggle probation status"""
        for employee in self:
            employee.is_probation = not employee.is_probation
            if employee.is_probation:
                employee.probation_start_date = fields.Date.today()
            else:
                employee.probation_start_date = False
                employee.probation_end_date = False
        return True
