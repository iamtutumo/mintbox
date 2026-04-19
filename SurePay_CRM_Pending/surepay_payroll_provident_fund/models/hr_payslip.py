from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'surepay_payroll.hr.payslip'

    provident_fund_amount = fields.Float(
        string='Provident Fund',
        compute='_compute_provident_fund_amount',
        store=True,
        help="Provident Fund deduction amount"
    )
    
    @api.depends('contract_id.has_provident_fund', 'contract_id.provident_fund_rate', 'line_ids')
    def _compute_provident_fund_amount(self):
        for payslip in self:
            if payslip.contract_id and payslip.contract_id.has_provident_fund:
                payslip.provident_fund_amount = payslip.contract_id._get_provident_fund_amount(payslip)
            else:
                payslip.provident_fund_amount = 0.0
    
    def compute_sheet(self):
        """Override to add Provident Fund deduction line"""
        result = super().compute_sheet()
        
        for payslip in self:
            # Remove existing PF lines
            pf_lines = payslip.line_ids.filtered(lambda line: line.code == 'PROVIDENT_FUND')
            if pf_lines:
                pf_lines.unlink()
            
            # Add PF deduction line if applicable
            if payslip.provident_fund_amount > 0:
                payslip.write({
                    'line_ids': [(0, 0, {
                        'name': 'Provident Fund',
                        'code': 'PROVIDENT_FUND',
                        'category_id': self.env.ref('hr_payroll.DED').id,
                        'sequence': 45,
                        'appears_on_payslip': True,
                        'amount': -payslip.provident_fund_amount,
                        'salary_rule_id': self._get_provident_fund_salary_rule().id,
                    })]
                })
        
        return result
    
    def _get_provident_fund_salary_rule(self):
        """Get or create the Provident Fund salary rule"""
        rule = self.env['hr.salary.rule'].search([
            ('code', '=', 'PROVIDENT_FUND'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not rule:
            # Create the Provident Fund salary rule
            structure = self.env['hr.payroll.structure'].search([
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if not structure:
                structure = self.env['hr.payroll.structure'].search([], limit=1)
            
            rule = self.env['hr.salary.rule'].create({
                'name': 'Provident Fund',
                'code': 'PROVIDENT_FUND',
                'category_id': self.env.ref('hr_payroll.DED').id,
                'sequence': 45,
                'appears_on_payslip': True,
                'amount_select': 'code',
                'amount_python_compute': 'result = payslip.provident_fund_amount',
                'struct_id': structure.id if structure else False,
                'company_id': self.company_id.id,
            })
        
        return rule
