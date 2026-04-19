from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class HrContract(models.Model):
    _inherit = 'hr.contract'

    prorata_calculation_method = fields.Selection([
        ('working_days', 'Working Days'),
        ('calendar_days', 'Calendar Days'),
    ], string='Prorata Calculation Method',
       default='working_days',
       help="Method to calculate prorata salary: based on working days or calendar days")
    
    include_weekends_in_prorata = fields.Boolean(
        string='Include Weekends in Prorata',
        default=False,
        help="Include weekends in prorata calculation when using working days method"
    )
    
    prorata_rounding_method = fields.Selection([
        ('nearest', 'Round to Nearest'),
        ('up', 'Round Up'),
        ('down', 'Round Down'),
    ], string='Prorata Rounding Method',
       default='nearest',
       help="Rounding method for prorata salary calculation")
    
    def _get_prorata_days(self, payslip):
        """Calculate prorata days for the payslip period"""
        self.ensure_one()
        
        if not payslip.date_from or not payslip.date_to:
            return 0.0, 0.0, 0.0  # actual_days, total_days, prorata_factor
        
        # Get employee's first working day and last working day
        employee = payslip.employee_id
        first_working_day = getattr(employee, 'first_working_day', False) or employee.create_date.date()
        last_working_day = employee.departure_date or False
        
        # Check if employee joined or left during the payslip period
        joined_mid_month = first_working_day > payslip.date_from
        left_mid_month = last_working_day and last_working_day < payslip.date_to
        
        if not joined_mid_month and not left_mid_month:
            # Full month - no prorata needed
            return 0.0, 0.0, 1.0
        
        # Calculate actual working days and total days
        if self.prorata_calculation_method == 'working_days':
            # Working days calculation
            if joined_mid_month and left_mid_month:
                # Employee both joined and left in the same period
                actual_days = self._get_working_days(first_working_day, last_working_day)
                total_days = self._get_working_days(payslip.date_from, payslip.date_to)
            elif joined_mid_month:
                # Employee joined during the period
                actual_days = self._get_working_days(first_working_day, payslip.date_to)
                total_days = self._get_working_days(payslip.date_from, payslip.date_to)
            elif left_mid_month:
                # Employee left during the period
                actual_days = self._get_working_days(payslip.date_from, last_working_day)
                total_days = self._get_working_days(payslip.date_from, payslip.date_to)
        else:
            # Calendar days calculation
            if joined_mid_month and left_mid_month:
                # Employee both joined and left in the same period
                actual_days = (last_working_day - first_working_day).days + 1
                total_days = (payslip.date_to - payslip.date_from).days + 1
            elif joined_mid_month:
                # Employee joined during the period
                actual_days = (payslip.date_to - first_working_day).days + 1
                total_days = (payslip.date_to - payslip.date_from).days + 1
            elif left_mid_month:
                # Employee left during the period
                actual_days = (last_working_day - payslip.date_from).days + 1
                total_days = (payslip.date_to - payslip.date_from).days + 1
        
        # Calculate prorata factor
        if total_days > 0:
            prorata_factor = actual_days / total_days
        else:
            prorata_factor = 1.0
        
        # Apply rounding
        prorata_factor = self._apply_rounding(prorata_factor)
        
        return actual_days, total_days, prorata_factor
    
    def _get_working_days(self, date_from, date_to):
        """Calculate number of working days between two dates"""
        if not date_from or not date_to:
            return 0
        
        working_days = 0
        current_date = date_from
        
        while current_date <= date_to:
            if self.include_weekends_in_prorata:
                working_days += 1
            else:
                # Exclude weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:
                    working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def _apply_rounding(self, value):
        """Apply rounding method to prorata factor"""
        if self.prorata_rounding_method == 'nearest':
            return round(value, 2)
        elif self.prorata_rounding_method == 'up':
            import math
            return math.ceil(value * 100) / 100
        elif self.prorata_rounding_method == 'down':
            import math
            return math.floor(value * 100) / 100
        else:
            return round(value, 2)
    
    def _get_prorata_salary_amount(self, payslip, basic_salary):
        """Calculate prorata salary amount"""
        self.ensure_one()
        
        actual_days, total_days, prorata_factor = self._get_prorata_days(payslip)
        
        if prorata_factor == 1.0:
            return basic_salary, actual_days, total_days, prorata_factor
        
        # Apply prorata to basic salary
        prorata_salary = basic_salary * prorata_factor
        
        return prorata_salary, actual_days, total_days, prorata_factor
