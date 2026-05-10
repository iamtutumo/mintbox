from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    medical_insurance_plan_id = fields.Many2one(
        'medical.insurance.plan',
        string='Medical Insurance Plan',
        help="Medical insurance plan for this contract"
    )

    medical_insurance_eligible = fields.Boolean(
        string='Medical Insurance Eligible',
        default=True,
        help="Whether employee is eligible for medical insurance under this contract"
    )

    medical_insurance_start_date = fields.Date(
        string='Medical Insurance Start Date',
        help="Start date of medical insurance coverage"
    )

    medical_insurance_end_date = fields.Date(
        string='Medical Insurance End Date',
        help="End date of medical insurance coverage"
    )

    employee_contribution_amount = fields.Float(
        string='Employee Contribution Amount',
        compute='_compute_medical_insurance_contribution',
        store=True,
        help="Monthly employee contribution for medical insurance"
    )

    employer_contribution_amount = fields.Float(
        string='Employer Contribution Amount',
        compute='_compute_medical_insurance_contribution',
        store=True,
        help="Monthly employer contribution for medical insurance"
    )

    total_medical_contribution = fields.Float(
        string='Total Medical Contribution',
        compute='_compute_medical_insurance_contribution',
        store=True,
        help="Total monthly contribution for medical insurance"
    )

    @api.depends('medical_insurance_plan_id.monthly_premium', 
                 'medical_insurance_plan_id.employee_contribution_rate',
                 'medical_insurance_plan_id.employer_contribution_rate',
                 'medical_insurance_eligible')
    def _compute_medical_insurance_contribution(self):
        for contract in self:
            if contract.medical_insurance_eligible and contract.medical_insurance_plan_id:
                premium = contract.medical_insurance_plan_id.monthly_premium
                employee_rate = contract.medical_insurance_plan_id.employee_contribution_rate / 100
                employer_rate = contract.medical_insurance_plan_id.employer_contribution_rate / 100
                
                contract.employee_contribution_amount = premium * employee_rate
                contract.employer_contribution_amount = premium * employer_rate
                contract.total_medical_contribution = premium
            else:
                contract.employee_contribution_amount = 0
                contract.employer_contribution_amount = 0
                contract.total_medical_contribution = 0

    @api.constrains('medical_insurance_start_date', 'medical_insurance_end_date')
    def _check_medical_insurance_dates(self):
        for contract in self:
            if contract.medical_insurance_start_date and contract.medical_insurance_end_date:
                if contract.medical_insurance_start_date > contract.medical_insurance_end_date:
                    raise ValueError("Medical insurance start date must be before end date")

    @api.onchange('medical_insurance_plan_id')
    def _onchange_medical_insurance_plan_id(self):
        """Set medical insurance dates based on plan dates"""
        if self.medical_insurance_plan_id:
            if not self.medical_insurance_start_date and self.medical_insurance_plan_id.coverage_start_date:
                self.medical_insurance_start_date = self.medical_insurance_plan_id.coverage_start_date
            if not self.medical_insurance_end_date and self.medical_insurance_plan_id.coverage_end_date:
                self.medical_insurance_end_date = self.medical_insurance_plan_id.coverage_end_date

    def get_medical_insurance_contribution_for_period(self, date_from, date_to):
        """
        Calculate medical insurance contribution for a specific period
        Returns tuple: (employee_contribution, employer_contribution)
        """
        self.ensure_one()
        
        if not self.medical_insurance_eligible or not self.medical_insurance_plan_id:
            return 0, 0

        # Check if the period overlaps with medical insurance coverage
        if self.medical_insurance_start_date and self.medical_insurance_start_date > date_to:
            return 0, 0
        if self.medical_insurance_end_date and self.medical_insurance_end_date < date_from:
            return 0, 0

        # Calculate prorated contribution if needed
        if (self.medical_insurance_start_date and self.medical_insurance_start_date >= date_from) or \
           (self.medical_insurance_end_date and self.medical_insurance_end_date <= date_to):
            
            # Calculate effective coverage period
            effective_from = max(self.medical_insurance_start_date or date_from, date_from)
            effective_to = min(self.medical_insurance_end_date or date_to, date_to)
            
            # Calculate number of days in coverage period
            total_days = (date_to - date_from).days + 1
            coverage_days = (effective_to - effective_from).days + 1
            
            # Prorate the contribution
            prorata_factor = coverage_days / total_days if total_days > 0 else 0
            
            employee_contribution = self.employee_contribution_amount * prorata_factor
            employer_contribution = self.employer_contribution_amount * prorata_factor
        else:
            # Full period contribution
            employee_contribution = self.employee_contribution_amount
            employer_contribution = self.employer_contribution_amount

        return employee_contribution, employer_contribution
