from odoo import models, fields, api

class MedicalInsurancePlan(models.Model):
    _name = 'medical.insurance.plan'
    _description = 'Medical Insurance Plan'
    _order = 'name'

    name = fields.Char(
        string='Plan Name',
        required=True,
        help="Name of the medical insurance plan"
    )

    code = fields.Char(
        string='Plan Code',
        required=True,
        help="Unique code for the medical insurance plan"
    )

    description = fields.Text(
        string='Description',
        help="Detailed description of the medical insurance plan"
    )

    insurance_provider = fields.Char(
        string='Insurance Provider',
        required=True,
        help="Name of the insurance provider"
    )

    policy_number = fields.Char(
        string='Policy Number',
        help="Policy number for the insurance plan"
    )

    coverage_amount = fields.Float(
        string='Coverage Amount',
        help="Maximum coverage amount per year"
    )

    employee_contribution_rate = fields.Float(
        string='Employee Contribution Rate (%)',
        default=0.0,
        help="Percentage of premium paid by employee"
    )

    employer_contribution_rate = fields.Float(
        string='Employer Contribution Rate (%)',
        default=100.0,
        help="Percentage of premium paid by employer"
    )

    monthly_premium = fields.Float(
        string='Monthly Premium',
        required=True,
        help="Monthly premium amount for the insurance plan"
    )

    deductible_amount = fields.Float(
        string='Deductible Amount',
        default=0.0,
        help="Annual deductible amount"
    )

    co_payment_percentage = fields.Float(
        string='Co-payment Percentage',
        default=0.0,
        help="Percentage of cost paid by employee after deductible"
    )

    max_out_of_pocket = fields.Float(
        string='Max Out of Pocket',
        help="Maximum out-of-pocket expense per year"
    )

    coverage_start_date = fields.Date(
        string='Coverage Start Date',
        help="Start date of coverage for this plan"
    )

    coverage_end_date = fields.Date(
        string='Coverage End Date',
        help="End date of coverage for this plan"
    )

    is_active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the plan is currently active"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help="Company that uses this insurance plan"
    )

    employee_ids = fields.One2many(
        'hr.employee',
        'medical_insurance_plan_id',
        string='Employees',
        help="Employees enrolled in this plan"
    )

    claim_ids = fields.One2many(
        'medical.insurance.claim',
        'insurance_plan_id',
        string='Claims',
        help="Claims made under this plan"
    )

    @api.constrains('employee_contribution_rate', 'employer_contribution_rate')
    def _check_contribution_rates(self):
        for plan in self:
            if plan.employee_contribution_rate + plan.employer_contribution_rate != 100:
                raise ValueError("Employee and employer contribution rates must sum to 100%")

    @api.constrains('co_payment_percentage')
    def _check_co_payment_percentage(self):
        for plan in self:
            if plan.co_payment_percentage < 0 or plan.co_payment_percentage > 100:
                raise ValueError("Co-payment percentage must be between 0 and 100")

    def name_get(self):
        result = []
        for plan in self:
            result.append((plan.id, f"{plan.name} ({plan.code})"))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
