from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    medical_insurance_plan_id = fields.Many2one(
        'medical.insurance.plan',
        string='Medical Insurance Plan',
        help="Medical insurance plan assigned to the employee"
    )

    medical_insurance_eligible = fields.Boolean(
        string='Medical Insurance Eligible',
        default=True,
        help="Whether employee is eligible for medical insurance"
    )

    medical_insurance_number = fields.Char(
        string='Medical Insurance Number',
        help="Employee's medical insurance policy number"
    )

    medical_insurance_start_date = fields.Date(
        string='Medical Insurance Start Date',
        help="Start date of employee's medical insurance coverage"
    )

    medical_insurance_end_date = fields.Date(
        string='Medical Insurance End Date',
        help="End date of employee's medical insurance coverage"
    )

    medical_insurance_card_issued = fields.Boolean(
        string='Medical Insurance Card Issued',
        default=False,
        help="Whether medical insurance card has been issued to employee"
    )

    medical_insurance_card_issue_date = fields.Date(
        string='Card Issue Date',
        help="Date when medical insurance card was issued"
    )

    dependents_covered = fields.Integer(
        string='Dependents Covered',
        default=0,
        help="Number of dependents covered under the insurance plan"
    )

    medical_claim_ids = fields.One2many(
        'medical.insurance.claim',
        'employee_id',
        string='Medical Claims',
        help="Medical claims made by the employee"
    )

    total_claims_amount = fields.Float(
        string='Total Claims Amount',
        compute='_compute_claim_statistics',
        store=True,
        help="Total amount of all claims made by employee"
    )

    approved_claims_amount = fields.Float(
        string='Approved Claims Amount',
        compute='_compute_claim_statistics',
        store=True,
        help="Total amount of approved claims"
    )

    pending_claims_count = fields.Integer(
        string='Pending Claims Count',
        compute='_compute_claim_statistics',
        store=True,
        help="Number of pending claims"
    )

    rejected_claims_count = fields.Integer(
        string='Rejected Claims Count',
        compute='_compute_claim_statistics',
        store=True,
        help="Number of rejected claims"
    )

    @api.depends('medical_claim_ids.total_amount', 'medical_claim_ids.approved_amount',
                 'medical_claim_ids.claim_status')
    def _compute_claim_statistics(self):
        for employee in self:
            claims = employee.medical_claim_ids
            employee.total_claims_amount = sum(claims.mapped('total_amount'))
            employee.approved_claims_amount = sum(claims.mapped('approved_amount'))
            employee.pending_claims_count = len(claims.filtered(lambda c: c.claim_status in ['submitted', 'under_review']))
            employee.rejected_claims_count = len(claims.filtered(lambda c: c.claim_status == 'rejected'))

    @api.constrains('medical_insurance_start_date', 'medical_insurance_end_date')
    def _check_medical_insurance_dates(self):
        for employee in self:
            if employee.medical_insurance_start_date and employee.medical_insurance_end_date:
                if employee.medical_insurance_start_date > employee.medical_insurance_end_date:
                    raise ValueError("Medical insurance start date must be before end date")

    @api.constrains('dependents_covered')
    def _check_dependents_covered(self):
        for employee in self:
            if employee.dependents_covered < 0:
                raise ValueError("Number of dependents covered cannot be negative")

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        """Update medical insurance information from contract"""
        if self.contract_id:
            self.medical_insurance_plan_id = self.contract_id.medical_insurance_plan_id
            self.medical_insurance_eligible = self.contract_id.medical_insurance_eligible
            self.medical_insurance_start_date = self.contract_id.medical_insurance_start_date
            self.medical_insurance_end_date = self.contract_id.medical_insurance_end_date

    def action_view_medical_claims(self):
        """
        Open medical claims for this employee
        """
        self.ensure_one()
        action = {
            'name': f'Medical Claims - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'medical.insurance.claim',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id}
        }
        if self.medical_insurance_plan_id:
            action['context']['default_insurance_plan_id'] = self.medical_insurance_plan_id.id
        return action

    def action_issue_medical_card(self):
        """
        Mark medical insurance card as issued
        """
        for employee in self:
            if not employee.medical_insurance_eligible:
                raise ValueError(f"Employee {employee.name} is not eligible for medical insurance")
            if not employee.medical_insurance_plan_id:
                raise ValueError(f"Employee {employee.name} has no medical insurance plan assigned")
            
            employee.write({
                'medical_insurance_card_issued': True,
                'medical_insurance_card_issue_date': fields.Date.today()
            })

    def action_revoke_medical_card(self):
        """
        Revoke medical insurance card
        """
        for employee in self:
            employee.write({
                'medical_insurance_card_issued': False,
                'medical_insurance_card_issue_date': False
            })

    def get_current_medical_coverage(self):
        """
        Get current medical insurance coverage details
        Returns dictionary with coverage information
        """
        self.ensure_one()
        
        if not self.medical_insurance_eligible or not self.medical_insurance_plan_id:
            return {
                'covered': False,
                'plan_name': False,
                'coverage_start': False,
                'coverage_end': False,
                'card_issued': False,
            }

        today = fields.Date.today()
        is_currently_covered = True
        
        if self.medical_insurance_start_date and self.medical_insurance_start_date > today:
            is_currently_covered = False
        if self.medical_insurance_end_date and self.medical_insurance_end_date < today:
            is_currently_covered = False

        return {
            'covered': is_currently_covered,
            'plan_name': self.medical_insurance_plan_id.name,
            'coverage_start': self.medical_insurance_start_date,
            'coverage_end': self.medical_insurance_end_date,
            'card_issued': self.medical_insurance_card_issued,
            'insurance_number': self.medical_insurance_number,
            'provider': self.medical_insurance_plan_id.insurance_provider,
        }
