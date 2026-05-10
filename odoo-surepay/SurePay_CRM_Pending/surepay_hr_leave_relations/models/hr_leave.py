from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, timedelta


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    
    is_surepay_custom = fields.Boolean(string='SurePay Custom Type', default=False)
    restrict_probation = fields.Boolean(string='Restrict for Probation Employees',
                                      default=False,
                                      help='Restrict this leave type for employees on probation')
    
    maternity_leave_days = fields.Integer(string='Maternity Leave Days',
                                         default=90,
                                         help='Number of days for maternity leave')
    
    paternity_leave_days = fields.Integer(string='Paternity Leave Days',
                                         default=5,
                                         help='Number of days for paternity leave')
    
    # requires_date_range = fields.Boolean(string='Requires Date Range',
    #                                    default=False,
    #                                    help='This leave type requires specific start and end dates')
    
    # max_duration_days = fields.Integer(string='Maximum Duration (Days)',
    #                                   default=0,
    #                                   help='Maximum duration in days for this leave type (0 = unlimited)')
    
    @api.constrains('maternity_leave_days')
    def _check_maternity_leave_days(self):
        for leave_type in self:
            if leave_type.maternity_leave_days < 0:
                raise ValidationError(_('Maternity leave days must be positive.'))
    
    @api.constrains('paternity_leave_days')
    def _check_paternity_leave_days(self):
        for leave_type in self:
            if leave_type.paternity_leave_days < 0:
                raise ValidationError(_('Paternity leave days must be positive.'))
    
    # @api.constrains('max_duration_days')
    # def _check_max_duration_days(self):
    #     for leave_type in self:
    #         if leave_type.max_duration_days < 0:
    #             raise ValidationError(_('Maximum duration days must be positive.'))


class HrLeave(models.Model):
    _inherit = 'hr.leave'
    
    is_annual_allocation = fields.Boolean(string='Annual Allocation',
                                         default=False,
                                         help='Indicates if this leave is part of annual allocation')
    
    allocation_year = fields.Integer(string='Allocation Year',
                                    compute='_compute_allocation_year',
                                    store=True)
    
    @api.depends('date_from')
    def _compute_allocation_year(self):
        for leave in self:
            if leave.date_from:
                leave.allocation_year = leave.date_from.year
            else:
                leave.allocation_year = False
    
    @api.model_create_multi
    def create(self, vals_list):
        leaves = super(HrLeave, self).create(vals_list)
        for leave in leaves:
            leave._check_probation_restriction()
        return leaves
    
    def write(self, vals):
        result = super(HrLeave, self).write(vals)
        for leave in self:
            leave._check_probation_restriction()
        return result
    
    def _check_probation_restriction(self):
        """Check if leave type is restricted for probation employees"""
        for leave in self:
            if leave.holiday_status_id.restrict_probation and leave.employee_id:
                if leave.employee_id.is_on_probation:
                    raise ValidationError(_(
                        'Employees on probation cannot apply for %s leave type.' % 
                        leave.holiday_status_id.name
                    ))
    
    # def _check_date_range_requirements(self):
    #     """Check if leave type requires date range and validate constraints"""
    #     for leave in self:
    #         if leave.holiday_status_id.requires_date_range:
    #             if not leave.date_from or not leave.date_to:
    #                 raise ValidationError(_(
    #                     '%s leave type requires both start and end dates.' % 
    #                     leave.holiday_status_id.name
    #                 ))
    #             
    #             if leave.holiday_status_id.max_duration_days > 0:
    #                 duration = (leave.date_to - leave.date_from).days + 1
    #                 if duration > leave.holiday_status_id.max_duration_days:
    #                     raise ValidationError(_(
    #                         '%s leave type cannot exceed %d days. Requested duration: %d days.' % (
    #                             leave.holiday_status_id.name,
    #                             leave.holiday_status_id.max_duration_days,
    #                             duration
    #                         )
    #                     ))
    
    @api.model
    def _create_annual_leave_allocation(self):
        """Create annual leave allocation for all employees"""
        current_year = fields.Date.today().year
        annual_leave_type = self.env.ref('surepay_hr_leave_relations.leave_type_annual')
        
        if not annual_leave_type:
            raise ValidationError(_('Annual leave type not found.'))
        
        # Get all active employees
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        for employee in employees:
            # Check if allocation already exists for this year
            existing_allocation = self.search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', annual_leave_type.id),
                ('allocation_year', '=', current_year),
                ('is_annual_allocation', '=', True)
            ])
            
            if not existing_allocation:
                # Create annual allocation
                self.create({
                    'name': f'Annual Leave Allocation {current_year}',
                    'employee_id': employee.id,
                    'holiday_status_id': annual_leave_type.id,
                    'date_from': f'{current_year}-01-01',
                    'date_to': f'{current_year}-12-31',
                    'number_of_days': 20,  # 20 days annual leave
                    'is_annual_allocation': True,
                    'state': 'validate'
                })
    
    @api.model
    def _reset_annual_leave_allocation(self):
        """Reset annual leave allocation at the end of year"""
        current_year = fields.Date.today().year
        next_year = current_year + 1
        
        # Archive current year's allocations
        current_allocations = self.search([
            ('allocation_year', '=', current_year),
            ('is_annual_allocation', '=', True)
        ])
        
        current_allocations.write({'active': False})
        
        # Create new allocations for next year
        self._create_annual_leave_allocation()
    
    def get_leave_balance(self, employee_id, leave_type_id):
        """Get leave balance for employee and leave type"""
        allocations = self.search([
            ('employee_id', '=', employee_id),
            ('holiday_status_id', '=', leave_type_id),
            ('state', '=', 'validate'),
            ('is_annual_allocation', '=', True)
        ])
        
        total_allocated = sum(allocation.number_of_days for allocation in allocations)
        
        # Get taken leaves
        taken_leaves = self.search([
            ('employee_id', '=', employee_id),
            ('holiday_status_id', '=', leave_type_id),
            ('state', '=', 'validate'),
            ('is_annual_allocation', '=', False)
        ])
        
        total_taken = sum(leave.number_of_days for leave in taken_leaves)
        
        return {
            'allocated': total_allocated,
            'taken': total_taken,
            'remaining': total_allocated - total_taken
        }
    
    @api.model
    def _send_leave_balance_notifications(self):
        """Send leave balance notifications to employees"""
        current_year = fields.Date.today().year
        annual_leave_type = self.env.ref('surepay_hr_leave_relations.leave_type_annual')
        
        if not annual_leave_type:
            return
        
        # Get all active employees
        employees = self.env['hr.employee'].search([('active', '=', True), ('work_email', '!=', False)])
        
        for employee in employees:
            balance = self.get_leave_balance(employee.id, annual_leave_type.id)
            
            # Send notification if remaining days are low (less than 5 days)
            if balance['remaining'] < 5 and balance['remaining'] >= 0:
                template = self.env.ref('surepay_hr_leave_relations.email_template_leave_balance_notification')
                if template:
                    template.send_mail(
                        employee.id,
                        email_values={
                            'email_to': employee.work_email,
                            'subject': f'Low Leave Balance Notification - {employee.name}',
                        }
                    )


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    
    is_annual_allocation = fields.Boolean(string='Annual Allocation',
                                         default=False,
                                         help='Indicates if this allocation is part of annual allocation')
    
    allocation_year = fields.Integer(string='Allocation Year',
                                    compute='_compute_allocation_year',
                                    store=True)
    
    @api.depends('date_from')
    def _compute_allocation_year(self):
        for allocation in self:
            if allocation.date_from:
                allocation.allocation_year = allocation.date_from.year
            else:
                allocation.allocation_year = False
