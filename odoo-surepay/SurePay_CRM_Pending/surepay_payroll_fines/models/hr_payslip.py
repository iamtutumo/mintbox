from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'surepay_payroll.hr.payslip'

    fine_ids = fields.One2many(
        'hr.fine', 'payslip_id',
        string='Fines',
        help="Fines deducted in this payslip"
    )
    
    total_fines = fields.Float(
        string='Total Fines',
        compute='_compute_total_fines',
        store=True,
        help="Total amount of fines deducted"
    )
    
    @api.depends('fine_ids.amount')
    def _compute_total_fines(self):
        for payslip in self:
            payslip.total_fines = sum(payslip.fine_ids.mapped('amount'))
    
    def action_payslip_done(self):
        """Override to process fines when payslip is confirmed"""
        result = super().action_payslip_done()
        
        # Process pending fines for this employee
        for payslip in self:
            pending_fines = self.env['hr.fine'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('state', '=', 'pending'),
                ('date', '<=', payslip.date_to),
            ])
            
            # Link fines to payslip and mark as deducted
            for fine in pending_fines:
                fine.write({
                    'payslip_id': payslip.id,
                    'state': 'deducted',
                })
        
        return result
    
    def compute_sheet(self):
        """Override to add fine deduction lines"""
        result = super().compute_sheet()
        
        for payslip in self:
            # Remove existing fine lines
            fine_lines = payslip.line_ids.filtered(lambda line: line.code == 'FINES')
            if fine_lines:
                fine_lines.unlink()
            
            # Add fine deduction line if there are fines
            if payslip.total_fines > 0:
                payslip.write({
                    'line_ids': [(0, 0, {
                        'name': 'Fines',
                        'code': 'FINES',
                        'category_id': self.env.ref('hr_payroll.DED').id,
                        'sequence': 50,
                        'appears_on_payslip': True,
                        'amount': -payslip.total_fines,
                        'salary_rule_id': self._get_fine_salary_rule().id,
                    })]
                })
        
        return result
    
    def _get_fine_salary_rule(self):
        """Get or create the fine salary rule"""
        rule = self.env['hr.salary.rule'].search([
            ('code', '=', 'FINES'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not rule:
            # Create the fine salary rule
            structure = self.env['hr.payroll.structure'].search([
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if not structure:
                structure = self.env['hr.payroll.structure'].search([], limit=1)
            
            rule = self.env['hr.salary.rule'].create({
                'name': 'Fines',
                'code': 'FINES',
                'category_id': self.env.ref('hr_payroll.DED').id,
                'sequence': 50,
                'appears_on_payslip': True,
                'amount_select': 'code',
                'amount_python_compute': 'result = payslip.total_fines',
                'struct_id': structure.id if structure else False,
                'company_id': self.company_id.id,
            })
        
        return rule
    
    def action_view_fines(self):
        """View fines related to this payslip"""
        self.ensure_one()
        
        action = {
            'name': 'Fines',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.fine',
            'view_mode': 'tree,form',
            'domain': [('payslip_id', '=', self.id)],
            'context': {'default_payslip_id': self.id},
        }
        
        if len(self.fine_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.fine_ids.id,
            })
        
        return action
