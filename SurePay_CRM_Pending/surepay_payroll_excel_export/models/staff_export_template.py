from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64

class StaffExportTemplate(models.Model):
    _name = 'staff.export.template'
    _description = 'Staff Export Template for Payroll Processing'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    code = fields.Char(string='Code', required=True, help="Unique code for the template")
    description = fields.Text(string='Description')
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)
    
    # Template sections configuration
    include_basic_info = fields.Boolean(string='Include Basic Information', default=True)
    include_employment_details = fields.Boolean(string='Include Employment Details', default=True)
    include_current_salary = fields.Boolean(string='Include Current Salary', default=True)
    include_allowances = fields.Boolean(string='Include Allowances', default=True)
    include_deductions = fields.Boolean(string='Include Deductions', default=True)
    include_fines = fields.Boolean(string='Include Fines', default=True)
    include_loans = fields.Boolean(string='Include Loans', default=True)
    include_tax_info = fields.Boolean(string='Include Tax Information', default=True)
    include_bank_details = fields.Boolean(string='Include Bank Details', default=True)
    
    # Editable fields configuration (for HR to fill in)
    editable_basic_salary = fields.Boolean(string='Editable Basic Salary', default=True)
    editable_allowances = fields.Boolean(string='Editable Allowances', default=True)
    editable_deductions = fields.Boolean(string='Editable Deductions', default=True)
    editable_fines = fields.Boolean(string='Editable Fines', default=True)
    editable_overtime = fields.Boolean(string='Editable Overtime', default=True)
    editable_bonus = fields.Boolean(string='Editable Bonus', default=True)
    editable_commission = fields.Boolean(string='Editable Commission', default=True)
    
    # Allowance types to include
    # Note: Using salary rule categories as allowance types since dedicated allowance type model doesn't exist
    allowance_type_ids = fields.Many2many('surepay_payroll.hr.salary.rule.category', 'staff_export_template_allowance_rel', 'template_id', 'allowance_type_id', string='Allowance Types',
                                        domain=[('code', 'in', ['ALW', 'BASIC', 'HOUSE', 'TRANSPORT', 'MEDICAL'])])
    
    # Deduction types to include  
    # Note: Using salary rule categories as deduction types since dedicated deduction type model doesn't exist
    deduction_type_ids = fields.Many2many('surepay_payroll.hr.salary.rule.category', 'staff_export_template_deduction_rel', 'template_id', 'deduction_type_id', string='Deduction Types',
                                        domain=[('code', 'in', ['DED', 'TAX', 'NSSF', 'NHIF', 'LOAN'])])
    
    # Fine types to include
    fine_type_ids = fields.Many2many('hr.fine.rule', 'staff_export_template_fine_rel', 'template_id', 'fine_type_id', string='Fine Types')
    
    # Excel formatting
    header_color = fields.Char(string='Header Color', default='#366092', help="Hex color code for headers")
    editable_color = fields.Char(string='Editable Fields Color', default='#FFC107', help="Hex color for editable fields")
    header_font_size = fields.Integer(string='Header Font Size', default=12)
    data_font_size = fields.Integer(string='Data Font Size', default=10)
    
    # Export settings
    file_prefix = fields.Char(string='File Prefix', default='Staff_Payroll_Data')
    include_company_logo = fields.Boolean(string='Include Company Logo', default=True)
    include_instructions = fields.Boolean(string='Include Instructions Sheet', default=True)
    include_validation_sheet = fields.Boolean(string='Include Validation Sheet', default=True)
    
    # Default values for new entries
    default_basic_salary = fields.Float(string='Default Basic Salary', default=0.0)
    default_working_days = fields.Integer(string='Default Working Days', default=26)
    default_overtime_rate = fields.Float(string='Default Overtime Rate', default=1.5)
    
    @api.constrains('code')
    def _check_code_unique(self):
        for template in self:
            existing = self.search([
                ('code', '=', template.code),
                ('id', '!=', template.id),
                ('company_id', '=', template.company_id.id)
            ])
            if existing:
                raise ValidationError(_('Template code must be unique per company'))

    def action_export_staff_data(self):
        """Export staff data using this template"""
        self.ensure_one()
        
        # Get all active employees
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        if not employees:
            raise UserError(_("No active employees found"))
        
        # Generate Excel file
        excel_data = self._generate_excel_file(employees)
        
        # Create attachment
        from datetime import date
        filename = f"{self.file_prefix}_{date.today().strftime('%Y%m%d')}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'res_model': 'staff.export.template',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    
    def _generate_excel_file(self, employees):
        """Generate Excel file with staff data"""
        # This would be implemented using openpyxl or similar library
        # For now, we'll return a mock implementation
        import io
        
        # Create a simple Excel file with basic structure
        excel_data = io.BytesIO()
        # In a real implementation, this would use openpyxl to create the Excel file
        excel_data.write(b"Mock Excel data")
        excel_data.seek(0)
        
        return excel_data.read()
