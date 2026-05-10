from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class StaffImportData(models.Model):
    _name = 'staff.import.data'
    _description = 'Staff Import Data for Payroll Processing'
    _order = 'import_date desc, employee_name'

    import_batch_id = fields.Many2one('staff.import.batch', string='Import Batch', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_code = fields.Char(string='Employee Code')
    employee_name = fields.Char(string='Employee Name')
    department = fields.Char(string='Department')
    position = fields.Char(string='Position')
    
    # Current salary data (from system)
    current_basic_salary = fields.Float(string='Current Basic Salary')
    current_house_allowance = fields.Float(string='Current House Allowance')
    current_transport_allowance = fields.Float(string='Current Transport Allowance')
    current_meal_allowance = fields.Float(string='Current Meal Allowance')
    current_other_allowances = fields.Float(string='Current Other Allowances')
    current_tax_deduction = fields.Float(string='Current Tax Deduction')
    current_nssf_deduction = fields.Float(string='Current NSSF Deduction')
    current_nhif_deduction = fields.Float(string='Current NHIF Deduction')
    current_loan_deduction = fields.Float(string='Current Loan Deduction')
    current_fine_deduction = fields.Float(string='Current Fine Deduction')
    
    # New salary data (from Excel import)
    new_basic_salary = fields.Float(string='New Basic Salary')
    new_house_allowance = fields.Float(string='New House Allowance')
    new_transport_allowance = fields.Float(string='New Transport Allowance')
    new_meal_allowance = fields.Float(string='New Meal Allowance')
    new_other_allowances = fields.Float(string='New Other Allowances')
    new_tax_deduction = fields.Float(string='New Tax Deduction')
    new_nssf_deduction = fields.Float(string='New NSSF Deduction')
    new_nhif_deduction = fields.Float(string='New NHIF Deduction')
    new_loan_deduction = fields.Float(string='New Loan Deduction')
    new_fine_deduction = fields.Float(string='New Fine Deduction')
    
    # Additional payroll data
    overtime_hours = fields.Float(string='Overtime Hours')
    overtime_rate = fields.Float(string='Overtime Rate')
    overtime_amount = fields.Float(string='Overtime Amount', compute='_compute_overtime_amount', store=True)
    
    bonus_amount = fields.Float(string='Bonus Amount')
    commission_amount = fields.Float(string='Commission Amount')
    other_earnings = fields.Float(string='Other Earnings')
    
    working_days = fields.Integer(string='Working Days')
    leave_days = fields.Integer(string='Leave Days')
    sick_days = fields.Integer(string='Sick Days')
    
    # Validation status
    validation_status = fields.Selection([
        ('draft', 'Draft'),
        ('valid', 'Valid'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], string='Validation Status', default='draft')
    
    validation_messages = fields.Text(string='Validation Messages')
    is_processed = fields.Boolean(string='Is Processed', default=False)
    
    # Import metadata
    import_date = fields.Datetime(string='Import Date', default=fields.Datetime.now)
    import_user_id = fields.Many2one('res.users', string='Imported By', default=lambda self: self.env.user)
    
    @api.depends('overtime_hours', 'overtime_rate')
    def _compute_overtime_amount(self):
        for record in self:
            record.overtime_amount = record.overtime_hours * record.overtime_rate if record.overtime_rate else 0
    
    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._validate_data()
        return record
    
    def write(self, vals):
        result = super().write(vals)
        for record in self:
            if any(field in vals for field in ['new_basic_salary', 'new_house_allowance', 'new_transport_allowance',
                                               'new_meal_allowance', 'new_other_allowances', 'overtime_hours',
                                               'overtime_rate', 'bonus_amount', 'commission_amount', 'working_days']):
                record._validate_data()
        return result
    
    def _validate_data(self):
        """Validate the imported data"""
        self.ensure_one()
        messages = []
        
        # Check employee mapping
        if not self.employee_id and self.employee_code:
            employee = self.env['hr.employee'].search([('code', '=', self.employee_code)], limit=1)
            if employee:
                self.employee_id = employee.id
                messages.append(f"✓ Employee found: {employee.name}")
            else:
                messages.append(f"⚠ Employee not found with code: {self.employee_code}")
                self.validation_status = 'warning'
        
        # Validate salary data
        if self.new_basic_salary and self.new_basic_salary < 0:
            messages.append("⚠ Basic salary cannot be negative")
            self.validation_status = 'warning'
        
        if self.new_basic_salary and self.new_basic_salary > 1000000:  # Reasonable upper limit
            messages.append("⚠ Basic salary seems unusually high")
            self.validation_status = 'warning'
        
        # Validate working days
        if self.working_days and (self.working_days < 0 or self.working_days > 31):
            messages.append("⚠ Working days must be between 0 and 31")
            self.validation_status = 'warning'
        
        # Validate overtime
        if self.overtime_hours and self.overtime_hours < 0:
            messages.append("⚠ Overtime hours cannot be negative")
            self.validation_status = 'warning'
        
        if self.overtime_rate and (self.overtime_rate < 1 or self.overtime_rate > 3):
            messages.append("⚠ Overtime rate should typically be between 1.0 and 3.0")
            self.validation_status = 'warning'
        
        # Check for significant changes
        if self.current_basic_salary and self.new_basic_salary:
            change_percent = abs(self.new_basic_salary - self.current_basic_salary) / self.current_basic_salary * 100
            if change_percent > 50:  # More than 50% change
                messages.append(f"⚠ Large salary change detected: {change_percent:.1f}%")
                self.validation_status = 'warning'
        
        self.validation_messages = '\n'.join(messages) if messages else '✓ All validations passed'
        
        if self.validation_status == 'draft':
            self.validation_status = 'valid'
    
    def action_revalidate(self):
        """Revalidate the data"""
        self._validate_data()
        return True
    
    def action_process_payroll(self):
        """Process this record for payroll"""
        if not self.employee_id:
            raise UserError(_("Employee must be mapped before processing payroll"))
        
        if self.validation_status == 'error':
            raise UserError(_("Cannot process record with validation errors"))
        
        # Create payslip or update existing one
        payslip = self._create_or_update_payslip()
        
        self.is_processed = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payslip',
            'res_model': 'surepay_payroll.hr.payslip',
            'res_id': payslip.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_validate_data(self):
        """Validate the staff data"""
        self.ensure_one()
        
        self._validate_data()
        return True
    
    def action_process_data(self):
        """Process the staff data and create/update payslip"""
        self.ensure_one()
        
        if self.validation_status not in ['valid', 'warning']:
            raise UserError(_("Data must be validated before processing"))
        
        self._create_or_update_payslip()
        return True
    
    def _create_or_update_payslip(self):
        """Create or update payslip with imported data"""
        # This would be implemented based on the SurePay payroll structure
        # For now, we'll create a basic implementation
        payslip_vals = {
            'employee_id': self.employee_id.id,
            'date_from': fields.Date.today().replace(day=1),  # First day of current month
            'date_to': fields.Date.today(),  # Today
            'struct_id': self.employee_id.contract_id.struct_id.id if self.employee_id.contract_id else False,
            'contract_id': self.employee_id.contract_id.id if self.employee_id.contract_id else False,
        }
        
        # Check if payslip already exists for this period
        existing_payslip = self.env['surepay_payroll.hr.payslip'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date_from', '=', payslip_vals['date_from']),
            ('date_to', '=', payslip_vals['date_to']),
        ], limit=1)
        
        if existing_payslip:
            payslip = existing_payslip
            # Update existing payslip with new data
            # This would need to be implemented based on SurePay payslip structure
        else:
            payslip = self.env['surepay_payroll.hr.payslip'].create(payslip_vals)
        
        return payslip
