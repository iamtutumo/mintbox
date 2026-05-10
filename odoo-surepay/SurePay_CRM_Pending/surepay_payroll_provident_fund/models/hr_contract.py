from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    has_provident_fund = fields.Boolean(
        string='Provident Fund',
        default=False,
        help="Whether employee contributes to Provident Fund"
    )
    
    provident_fund_rate = fields.Float(
        string='PF Rate (%)',
        default=5.0,
        help="Provident Fund contribution rate as percentage of basic salary"
    )
    
    provident_fund_max_amount = fields.Float(
        string='PF Max Amount',
        help="Maximum Provident Fund contribution amount per month"
    )
    
    @api.onchange('has_provident_fund')
    def _onchange_has_provident_fund(self):
        """Set default PF rate when enabled"""
        if self.has_provident_fund and not self.provident_fund_rate:
            self.provident_fund_rate = 5.0
    
    def _get_provident_fund_amount(self, payslip):
        """Calculate Provident Fund amount for payslip"""
        self.ensure_one()
        
        if not self.has_provident_fund or not self.provident_fund_rate:
            return 0.0
        
        # Get basic salary from payslip
        basic_salary = 0.0
        for line in payslip.line_ids:
            if line.code == 'BASIC':
                basic_salary = line.total
                break
        
        # Calculate PF amount
        pf_amount = (basic_salary * self.provident_fund_rate) / 100
        
        # Apply maximum limit if set
        if self.provident_fund_max_amount:
            pf_amount = min(pf_amount, self.provident_fund_max_amount)
        
        return pf_amount
