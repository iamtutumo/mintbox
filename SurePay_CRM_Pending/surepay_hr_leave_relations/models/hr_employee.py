from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    exit_clearance_count = fields.Integer(string='Exit Clearances', compute='_compute_exit_clearance_count')
    grievance_count = fields.Integer(string='Grievances', compute='_compute_grievance_count')
    leave_balance_count = fields.Integer(string='Leave Balance', compute='_compute_leave_balance_count')
    
    def _compute_exit_clearance_count(self):
        for employee in self:
            employee.exit_clearance_count = self.env['hr.exit.clearance'].search_count([('employee_id', '=', employee.id)])
    
    def _compute_grievance_count(self):
        for employee in self:
            employee.grievance_count = self.env['hr.grievance'].search_count([('employee_id', '=', employee.id)])
    
    def _compute_leave_balance_count(self):
        for employee in self:
            # Count active leave allocations
            employee.leave_balance_count = self.env['hr.leave.allocation'].search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.active', '=', True)
            ])
    
    def action_view_exit_clearances(self):
        self.ensure_one()
        action = self.env.ref('surepay_hr_leave_relations.action_hr_exit_clearance').read()[0]
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = {'default_employee_id': self.id}
        return action
    
    def action_view_grievances(self):
        self.ensure_one()
        action = self.env.ref('surepay_hr_leave_relations.action_hr_grievance').read()[0]
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = {'default_employee_id': self.id}
        return action
    
    def action_view_leave_balance(self):
        self.ensure_one()
        action = self.env.ref('hr_holidays.hr_leave_allocation_action').read()[0]
        action['domain'] = [('employee_id', '=', self.id), ('state', '=', 'validate')]
        action['context'] = {'default_employee_id': self.id}
        return action
