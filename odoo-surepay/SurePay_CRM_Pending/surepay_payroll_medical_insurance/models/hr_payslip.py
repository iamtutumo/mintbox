from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'surepay_payroll.hr.payslip'

    medical_insurance_employee_deduction = fields.Float(
        string='Medical Insurance Employee Deduction',
        compute='_compute_medical_insurance_deductions',
        store=True,
        help="Employee's contribution to medical insurance"
    )

    medical_insurance_employer_contribution = fields.Float(
        string='Medical Insurance Employer Contribution',
        compute='_compute_medical_insurance_deductions',
        store=True,
        help="Employer's contribution to medical insurance"
    )

    medical_insurance_plan_id = fields.Many2one(
        'medical.insurance.plan',
        string='Medical Insurance Plan',
        compute='_compute_medical_insurance_deductions',
        store=True,
        help="Medical insurance plan for this payslip"
    )

    medical_insurance_eligible = fields.Boolean(
        string='Medical Insurance Eligible',
        compute='_compute_medical_insurance_deductions',
        store=True,
        help="Whether employee is eligible for medical insurance in this payslip"
    )

    @api.depends('contract_id.medical_insurance_plan_id', 'contract_id.medical_insurance_eligible',
                 'contract_id.employee_contribution_amount', 'contract_id.employer_contribution_amount',
                 'date_from', 'date_to', 'employee_id.medical_insurance_eligible')
    def _compute_medical_insurance_deductions(self):
        for payslip in self:
            if payslip.contract_id and payslip.contract_id.medical_insurance_eligible:
                payslip.medical_insurance_plan_id = payslip.contract_id.medical_insurance_plan_id
                payslip.medical_insurance_eligible = payslip.contract_id.medical_insurance_eligible
                
                # Calculate prorated contributions for the payslip period
                employee_contrib, employer_contrib = payslip.contract_id.get_medical_insurance_contribution_for_period(
                    payslip.date_from, payslip.date_to
                )
                
                payslip.medical_insurance_employee_deduction = employee_contrib
                payslip.medical_insurance_employer_contribution = employer_contrib
            else:
                payslip.medical_insurance_plan_id = False
                payslip.medical_insurance_eligible = False
                payslip.medical_insurance_employee_deduction = 0
                payslip.medical_insurance_employer_contribution = 0

    def compute_sheet(self):
        """
        Override compute_sheet to add medical insurance deductions
        """
        # Call the original compute_sheet method
        result = super(HrPayslip, self).compute_sheet()
        
        # Add medical insurance deductions to the payslip
        for payslip in self:
            if payslip.medical_insurance_eligible and payslip.medical_insurance_employee_deduction > 0:
                # Get or create medical insurance deduction rule
                medical_rule = payslip._get_medical_insurance_rule()
                
                if medical_rule:
                    # Add medical insurance deduction to worked days
                    worked_days_lines = payslip.worked_days_line_ids
                    medical_line_exists = any(line.code == 'MEDICAL_INS' for line in worked_days_lines)
                    
                    if not medical_line_exists:
                        payslip.worked_days_line_ids = [(0, 0, {
                            'name': 'Medical Insurance Deduction',
                            'code': 'MEDICAL_INS',
                            'number_of_days': 1,
                            'number_of_hours': 0,
                            'contract_id': payslip.contract_id.id,
                            'amount': -payslip.medical_insurance_employee_deduction,
                        })]
                    
                    # Add medical insurance employer contribution as a benefit
                    if payslip.medical_insurance_employer_contribution > 0:
                        benefit_line_exists = any(line.code == 'MEDICAL_BEN' for line in worked_days_lines)
                        
                        if not benefit_line_exists:
                            payslip.worked_days_line_ids = [(0, 0, {
                                'name': 'Medical Insurance Benefit',
                                'code': 'MEDICAL_BEN',
                                'number_of_days': 1,
                                'number_of_hours': 0,
                                'contract_id': payslip.contract_id.id,
                                'amount': payslip.medical_insurance_employer_contribution,
                            })]
        
        return result

    def _get_medical_insurance_rule(self):
        """
        Get or create medical insurance salary rule
        """
        self.ensure_one()
        
        # Look for existing medical insurance rule
        rule = self.env['hr.salary.rule'].search([
            ('code', '=', 'MEDICAL_INS'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not rule:
            # Create the medical insurance rule if it doesn't exist
            rule_category = self.env['hr.salary.rule.category'].search([
                ('code', '=', 'DED'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if not rule_category:
                # Create deduction category if it doesn't exist
                rule_category = self.env['hr.salary.rule.category'].create({
                    'name': 'Deductions',
                    'code': 'DED',
                    'company_id': self.company_id.id,
                })
            
            rule = self.env['hr.salary.rule'].create({
                'name': 'Medical Insurance Deduction',
                'code': 'MEDICAL_INS',
                'category_id': rule_category.id,
                'sequence': 150,
                'condition_select': 'none',
                'amount_select': 'code',
                'amount_python_compute': 'result = inputs.MEDICAL_INS.amount if inputs.MEDICAL_INS else 0',
                'appears_on_payslip': True,
                'company_id': self.company_id.id,
            })
        
        return rule

    def action_view_medical_insurance_details(self):
        """
        Open medical insurance details for this payslip
        """
        self.ensure_one()
        
        if not self.medical_insurance_eligible:
            return {
                'type': 'ir.actions.act_window_close',
                'message': 'Employee is not eligible for medical insurance',
            }
        
        return {
            'name': f'Medical Insurance Details - {self.employee_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
            'context': {'active_id': self.contract_id.id},
        }

    def get_medical_insurance_summary(self):
        """
        Get medical insurance summary for the payslip
        Returns dictionary with insurance details
        """
        self.ensure_one()
        
        if not self.medical_insurance_eligible:
            return {
                'eligible': False,
                'plan_name': False,
                'employee_deduction': 0,
                'employer_contribution': 0,
                'total_contribution': 0,
            }
        
        return {
            'eligible': True,
            'plan_name': self.medical_insurance_plan_id.name,
            'provider': self.medical_insurance_plan_id.insurance_provider,
            'employee_deduction': self.medical_insurance_employee_deduction,
            'employer_contribution': self.medical_insurance_employer_contribution,
            'total_contribution': self.medical_insurance_employee_deduction + self.medical_insurance_employer_contribution,
            'coverage_start': self.contract_id.medical_insurance_start_date,
            'coverage_end': self.contract_id.medical_insurance_end_date,
        }
