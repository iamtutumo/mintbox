from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PayrollExportWizard(models.TransientModel):
    _name = 'payroll.export.wizard'
    _description = 'Payroll Export Wizard'

    export_type = fields.Selection([
        ('selected', 'Selected Payslips'),
        ('all', 'All Payslips'),
        ('by_period', 'By Period'),
        ('by_department', 'By Department'),
        ('by_employee', 'By Employee'),
    ], string='Export Type', required=True, default='selected')
    
    template_id = fields.Many2one('payroll.export.template', string='Export Template', required=True,
                                  domain="[('company_id', '=', company_id)]")
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Date filters
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    
    # Department filter
    department_id = fields.Many2one('hr.department', string='Department')
    
    # Employee filter
    employee_id = fields.Many2one('hr.employee', string='Employee')
    
    # Payslip selection
    payslip_ids = fields.Many2many('surepay_payroll.hr.payslip', string='Payslips')
    
    # Export options
    include_draft = fields.Boolean(string='Include Draft Payslips', default=False)
    include_paid = fields.Boolean(string='Include Paid Payslips', default=True)
    include_done = fields.Boolean(string='Include Done Payslips', default=True)
    
    # File options
    file_name = fields.Char(string='File Name', default='Payroll_Export')
    include_header = fields.Boolean(string='Include Header', default=True)
    include_footer = fields.Boolean(string='Include Footer', default=True)
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        
        # Get selected payslips from context
        if self.env.context.get('active_model') == 'surepay_payroll.hr.payslip':
            payslip_ids = self.env.context.get('active_ids', [])
            if payslip_ids:
                res['payslip_ids'] = payslip_ids
                res['export_type'] = 'selected'
        
        # Get default template
        default_template = self.env['payroll.export.template'].search([
            ('company_id', '=', self.env.company.id),
            ('active', '=', True)
        ], limit=1)
        if default_template:
            res['template_id'] = default_template.id
        
        return res
    
    @api.onchange('export_type')
    def _onchange_export_type(self):
        if self.export_type != 'selected':
            self.payslip_ids = False
    
    def action_export(self):
        """Export payroll data based on wizard settings"""
        # Get payslips to export
        payslips = self._get_payslips_to_export()
        
        if not payslips:
            raise UserError(_("No payslips found matching your criteria."))
        
        # Export using selected template
        return self.template_id.action_export_with_template(payslips)
    
    def _get_payslips_to_export(self):
        """Get payslips based on export type and filters"""
        domain = []
        
        # Apply export type filters
        if self.export_type == 'selected':
            if not self.payslip_ids:
                raise UserError(_("Please select payslips to export."))
            domain.append(('id', 'in', self.payslip_ids.ids))
        
        elif self.export_type == 'all':
            pass  # No additional filters
        
        elif self.export_type == 'by_period':
            if not self.date_from or not self.date_to:
                raise UserError(_("Please specify date range for period export."))
            domain.extend([
                ('date_from', '>=', self.date_from),
                ('date_to', '<=', self.date_to),
            ])
        
        elif self.export_type == 'by_department':
            if not self.department_id:
                raise UserError(_("Please select a department for export."))
            domain.append(('employee_id.department_id', '=', self.department_id.id))
        
        elif self.export_type == 'by_employee':
            if not self.employee_id:
                raise UserError(_("Please select an employee for export."))
            domain.append(('employee_id', '=', self.employee_id.id))
        
        # Apply status filters
        status_domain = []
        if self.include_draft:
            status_domain.append(('state', '=', 'draft'))
        if self.include_paid:
            status_domain.append(('state', '=', 'paid'))
        if self.include_done:
            status_domain.append(('state', '=', 'done'))
        
        if status_domain:
            if len(status_domain) == 1:
                domain.append(status_domain[0])
            else:
                domain.append('|' * (len(status_domain) - 1))
                domain.extend(status_domain)
        
        # Apply company filter
        domain.append(('company_id', '=', self.company_id.id))
        
        # Search payslips
        payslips = self.env['surepay_payroll.hr.payslip'].search(domain)
        
        return payslips
    
    def action_preview(self):
        """Preview payslips that will be exported"""
        payslips = self._get_payslips_to_export()
        
        if not payslips:
            raise UserError(_("No payslips found matching your criteria."))
        
        return {
            'name': _('Preview Export'),
            'type': 'ir.actions.act_window',
            'res_model': 'surepay_payroll.hr.payslip',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payslips.ids)],
            'context': {'active_test': False},
        }
    
    def action_create_template(self):
        """Create a new export template"""
        return {
            'name': _('Create Export Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'payroll.export.template',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': self.company_id.id,
            },
        }
