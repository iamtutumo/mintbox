from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'surepay_payroll.hr.payslip'

    prorata_days_worked = fields.Float(
        string='Prorata Days Worked',
        compute='_compute_prorata_info',
        store=True,
        help="Number of days worked in prorata calculation"
    )
    
    prorata_total_days = fields.Float(
        string='Prorata Total Days',
        compute='_compute_prorata_info',
        store=True,
        help="Total days in payslip period for prorata calculation"
    )
    
    prorata_factor = fields.Float(
        string='Prorata Factor',
        compute='_compute_prorata_info',
        store=True,
        help="Prorata factor applied to salary calculation"
    )
    
    is_prorata = fields.Boolean(
        string='Is Prorata',
        compute='_compute_prorata_info',
        store=True,
        help="Whether this payslip uses prorata salary calculation"
    )
    
    @api.depends('contract_id.prorata_calculation_method', 'employee_id.create_date', 
                 'employee_id.departure_date', 'date_from', 'date_to')
    def _compute_prorata_info(self):
        for payslip in self:
            if payslip.contract_id:
                actual_days, total_days, prorata_factor = payslip.contract_id._get_prorata_days(payslip)
                payslip.prorata_days_worked = actual_days
                payslip.prorata_total_days = total_days
                payslip.prorata_factor = prorata_factor
                payslip.is_prorata = prorata_factor != 1.0
            else:
                payslip.prorata_days_worked = 0.0
                payslip.prorata_total_days = 0.0
                payslip.prorata_factor = 1.0
                payslip.is_prorata = False
    
    def compute_sheet(self):
        """Override to apply prorata salary calculation"""
        result = super().compute_sheet()
        
        for payslip in self:
            if payslip.is_prorata and payslip.contract_id:
                # Get basic salary from payslip lines
                basic_salary = 0.0
                basic_line = False
                for line in payslip.line_ids:
                    if line.code == 'BASIC':
                        basic_salary = line.total
                        basic_line = line
                        break
                
                if basic_line and basic_salary > 0:
                    # Calculate prorata salary
                    prorata_salary, actual_days, total_days, prorata_factor = \
                        payslip.contract_id._get_prorata_salary_amount(payslip, basic_salary)
                    
                    # Update basic salary line with prorata amount
                    if prorata_salary != basic_salary:
                        basic_line.write({
                            'total': prorata_salary,
                            'amount': prorata_salary,
                        })
                        
                        # Add prorata adjustment line for transparency
                        payslip.write({
                            'line_ids': [(0, 0, {
                                'name': 'Prorata Salary Adjustment',
                                'code': 'PRORATA_ADJUST',
                                'category_id': self.env.ref('hr_payroll.ALW').id,
                                'sequence': 5,
                                'appears_on_payslip': True,
                                'amount': prorata_salary - basic_salary,
                                'salary_rule_id': self._get_prorata_salary_rule().id,
                                'note': f'Prorata calculation: {actual_days}/{total_days} days (Factor: {prorata_factor})',
                            })]
                        })
                        
                        # Recalculate payslip totals after prorata adjustment
                        payslip._compute_total()
        
        return result
    
    def _get_prorata_salary_rule(self):
        """Get or create the Prorata salary rule"""
        rule = self.env['hr.salary.rule'].search([
            ('code', '=', 'PRORATA_ADJUST'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not rule:
            # Create the Prorata salary rule
            structure = self.env['hr.payroll.structure'].search([
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if not structure:
                structure = self.env['hr.payroll.structure'].search([], limit=1)
            
            rule = self.env['hr.salary.rule'].create({
                'name': 'Prorata Salary Adjustment',
                'code': 'PRORATA_ADJUST',
                'category_id': self.env.ref('hr_payroll.ALW').id,
                'sequence': 5,
                'appears_on_payslip': True,
                'amount_select': 'code',
                'amount_python_compute': 'result = 0.0  # This will be set manually',
                'struct_id': structure.id if structure else False,
                'company_id': self.company_id.id,
                'note': 'Automatic adjustment for prorata salary calculation',
            })
        
        return rule
    
    def action_view_prorata_details(self):
        """View prorata calculation details"""
        self.ensure_one()
        
        if not self.is_prorata:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Prorata Details',
                    'message': 'This payslip does not use prorata calculation.',
                    'type': 'info',
                }
            }
        
        return {
            'name': 'Prorata Calculation Details',
            'type': 'ir.actions.act_window',
            'res_model': 'surepay_payroll.hr.payslip',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('surepay_payroll.hr_payslip_view_form').id,
            'target': 'current',
            'context': {
                'active_id': self.id,
                'active_model': 'surepay_payroll.hr.payslip',
            },
        }
