from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class StaffImportBatch(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'staff.import.batch'
    _description = 'Staff Import Batch for Payroll Processing'
    _order = 'create_date desc'

    name = fields.Char(string='Batch Name', required=True)
    description = fields.Text(string='Description')
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Import file information
    import_file = fields.Binary(string='Import File', required=True)
    import_filename = fields.Char(string='Filename')
    
    # Template used for import
    template_id = fields.Many2one('staff.export.template', string='Template', required=True)
    
    # Batch status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('imported', 'Imported'),
        ('validated', 'Validated'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    
    # Import statistics
    total_records = fields.Integer(string='Total Records', compute='_compute_statistics')
    valid_records = fields.Integer(string='Valid Records', compute='_compute_statistics')
    warning_records = fields.Integer(string='Warning Records', compute='_compute_statistics')
    error_records = fields.Integer(string='Error Records', compute='_compute_statistics')
    processed_records = fields.Integer(string='Processed Records', compute='_compute_statistics')
    
    # Payroll processing
    payroll_period_start = fields.Date(string='Payroll Period Start')
    payroll_period_end = fields.Date(string='Payroll Period End')
    payslip_batch_id = fields.Many2one('surepay_payroll.hr.payslip.run', string='Payslip Batch')
    payslip_count = fields.Integer(string='Payslips Count', compute='_compute_payslip_count')
    
    # Email settings
    send_payslips_email = fields.Boolean(string='Send Payslips by Email', default=True)
    email_template_id = fields.Many2one('mail.template', string='Email Template',
                                       domain="[('model', '=', 'surepay_payroll.hr.payslip')]")
    
    # Metadata
    create_date = fields.Datetime(string='Create Date', readonly=True)
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)
    import_date = fields.Datetime(string='Import Date', readonly=True)
    import_user_id = fields.Many2one('res.users', string='Imported By', readonly=True)
    
    # Related records
    staff_data_ids = fields.One2many('staff.import.data', 'import_batch_id', string='Staff Data')
    
    @api.depends('staff_data_ids.validation_status', 'staff_data_ids.is_processed')
    def _compute_statistics(self):
        for batch in self:
            staff_data = batch.staff_data_ids
            batch.total_records = len(staff_data)
            batch.valid_records = len(staff_data.filtered(lambda r: r.validation_status == 'valid'))
            batch.warning_records = len(staff_data.filtered(lambda r: r.validation_status == 'warning'))
            batch.error_records = len(staff_data.filtered(lambda r: r.validation_status == 'error'))
            batch.processed_records = len(staff_data.filtered(lambda r: r.is_processed))
    
    @api.depends('payslip_batch_id')
    def _compute_payslip_count(self):
        for batch in self:
            if batch.payslip_batch_id:
                payslips = self.env['surepay_payroll.hr.payslip'].search([('batch_id', '=', batch.payslip_batch_id.id)])
                batch.payslip_count = len(payslips)
            else:
                batch.payslip_count = 0
    
    @api.model
    def create(self, vals):
        batch = super().create(vals)
        if vals.get('import_file'):
            batch._process_import_file()
        return batch
    
    def write(self, vals):
        result = super().write(vals)
        if vals.get('import_file'):
            for batch in self:
                batch._process_import_file()
        return batch
    
    def _process_import_file(self):
        """Process the uploaded Excel file"""
        self.ensure_one()
        
        try:
            # Clear existing data
            self.staff_data_ids.unlink()
            
            # Process Excel file
            import_data = self._read_excel_file(self.import_file, self.import_filename)
            
            # Create staff import data records
            for row_data in import_data:
                staff_data_vals = self._prepare_staff_data_vals(row_data)
                self.env['staff.import.data'].create(staff_data_vals)
            
            self.state = 'imported'
            self.import_date = fields.Datetime.now()
            self.import_user_id = self.env.user
            
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            
        except Exception as e:
            _logger.error(f"Error processing import file: {str(e)}")
            raise UserError(_("Error processing import file: %s") % str(e))
    
    def _read_excel_file(self, file_data, filename):
        """Read Excel file and return data rows"""
        # This would be implemented using openpyxl or similar library
        # For now, we'll return a mock structure
        return [
            {
                'employee_code': 'EMP001',
                'employee_name': 'John Doe',
                'department': 'IT',
                'position': 'Developer',
                'current_basic_salary': 50000,
                'new_basic_salary': 55000,
                'new_house_allowance': 15000,
                'new_transport_allowance': 5000,
                'overtime_hours': 10,
                'overtime_rate': 1.5,
                'working_days': 26,
            }
        ]
    
    def _prepare_staff_data_vals(self, row_data):
        """Prepare staff data values from Excel row"""
        vals = {
            'import_batch_id': self.id,
            'employee_code': row_data.get('employee_code'),
            'employee_name': row_data.get('employee_name'),
            'department': row_data.get('department'),
            'position': row_data.get('position'),
            'current_basic_salary': row_data.get('current_basic_salary', 0),
            'new_basic_salary': row_data.get('new_basic_salary', 0),
            'new_house_allowance': row_data.get('new_house_allowance', 0),
            'new_transport_allowance': row_data.get('new_transport_allowance', 0),
            'new_meal_allowance': row_data.get('new_meal_allowance', 0),
            'new_other_allowances': row_data.get('new_other_allowances', 0),
            'overtime_hours': row_data.get('overtime_hours', 0),
            'overtime_rate': row_data.get('overtime_rate', 1.5),
            'working_days': row_data.get('working_days', 26),
        }
        return vals
    
    def action_validate_all(self):
        """Validate all records in the batch"""
        self.ensure_one()
        
        for staff_data in self.staff_data_ids:
            staff_data._validate_data()
        
        self.state = 'validated'
        return True
    
    def action_process_batch(self):
        """Process the entire batch for payroll"""
        self.ensure_one()
        
        if self.state != 'validated':
            raise UserError(_("Batch must be validated before processing"))
        
        if not self.payroll_period_start or not self.payroll_period_end:
            raise UserError(_("Payroll period dates must be selected"))
        
        if self.payroll_period_start > self.payroll_period_end:
            raise UserError(_("Payroll period start date must be before end date"))
        
        self.state = 'processing'
        
        # Process each staff record
        payslips = []
        for staff_data in self.staff_data_ids.filtered(lambda r: r.validation_status in ['valid', 'warning']):
            try:
                payslip = staff_data._create_or_update_payslip()
                payslips.append(payslip)
            except Exception as e:
                _logger.error(f"Error processing staff data {staff_data.id}: {str(e)}")
                staff_data.validation_status = 'error'
                staff_data.validation_messages = f"Processing error: {str(e)}"
        
        # Create payslip batch if multiple payslips were created
        if len(payslips) > 1:
            batch_vals = {
                'name': f"{self.name} - {self.payroll_period_start} to {self.payroll_period_end}",
                'date_start': self.payroll_period_start,
                'date_end': self.payroll_period_end,
                'company_id': self.company_id.id,
            }
            self.payslip_batch_id = self.env['surepay_payroll.payslip.batch'].create(batch_vals)
            
            # Add payslips to batch
            for payslip in payslips:
                payslip.batch_id = self.payslip_batch_id.id
        
        # Send payslips by email if requested
        if self.send_payslips_email and payslips:
            self._send_payslips_email(payslips)
        
        self.state = 'completed'
        return True
    
    def _send_payslips_email(self, payslips):
        """Send payslips by email"""
        for payslip in payslips:
            if payslip.employee_id.work_email:
                try:
                    template = self.email_template_id or self.env.ref('surepay_payroll.email_template_payslip')
                    template.send_mail(payslip.id, email_values={
                        'email_to': payslip.employee_id.work_email,
                    })
                except Exception as e:
                    _logger.error(f"Error sending payslip email to {payslip.employee_id.work_email}: {str(e)}")
    
    def action_cancel(self):
        """Cancel the batch"""
        self.state = 'cancelled'
        return True
    
    def action_reset_to_draft(self):
        """Reset batch to draft state"""
        self.state = 'draft'
        self.staff_data_ids.unlink()
        return True
    
    def action_view_payslips(self):
        """View payslips created from this batch"""
        self.ensure_one()
        
        if not self.payslip_batch_id:
            return
        
        payslips = self.env['surepay_payroll.hr.payslip'].search([('batch_id', '=', self.payslip_batch_id.id)])
        
        if not payslips:
            return
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payslips',
            'res_model': 'surepay_payroll.hr.payslip',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payslips.ids)],
            'context': {'default_batch_id': self.payslip_batch_id.id},
        }
    
    def action_view_staff_data(self):
        """View staff data in this batch"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Staff Data',
            'res_model': 'staff.import.data',
            'view_mode': 'tree,form',
            'domain': [('import_batch_id', '=', self.id)],
            'context': {'default_import_batch_id': self.id, 'search_default_unprocessed': 1},
        }
