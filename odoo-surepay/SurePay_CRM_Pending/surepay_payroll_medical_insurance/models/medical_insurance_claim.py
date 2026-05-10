from odoo import models, fields, api
from datetime import datetime

class MedicalInsuranceClaim(models.Model):
    _name = 'medical.insurance.claim'
    _description = 'Medical Insurance Claim'
    _order = 'claim_date desc'

    name = fields.Char(
        string='Claim Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_claim_reference(),
        help="Unique reference number for the claim"
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        help="Employee making the claim"
    )

    insurance_plan_id = fields.Many2one(
        'medical.insurance.plan',
        string='Insurance Plan',
        required=True,
        help="Insurance plan under which the claim is made"
    )

    claim_date = fields.Date(
        string='Claim Date',
        required=True,
        default=fields.Date.today,
        help="Date when the claim was submitted"
    )

    treatment_date = fields.Date(
        string='Treatment Date',
        required=True,
        help="Date when the medical treatment was received"
    )

    claim_type = fields.Selection([
        ('hospitalization', 'Hospitalization'),
        ('outpatient', 'Outpatient'),
        ('emergency', 'Emergency'),
        ('dental', 'Dental'),
        ('vision', 'Vision'),
        ('maternity', 'Maternity'),
        ('pharmacy', 'Pharmacy'),
        ('other', 'Other'),
    ], string='Claim Type',
       required=True,
       help="Type of medical claim"
    )

    description = fields.Text(
        string='Description',
        required=True,
        help="Detailed description of the medical treatment and claim"
    )

    diagnosis = fields.Text(
        string='Diagnosis',
        help="Medical diagnosis for the claim"
    )

    hospital_name = fields.Char(
        string='Hospital/Clinic Name',
        help="Name of hospital or clinic where treatment was received"
    )

    doctor_name = fields.Char(
        string='Doctor Name',
        help="Name of the treating doctor"
    )

    total_amount = fields.Float(
        string='Total Amount',
        required=True,
        help="Total amount claimed"
    )

    approved_amount = fields.Float(
        string='Approved Amount',
        help="Amount approved by insurance company"
    )

    employee_share = fields.Float(
        string='Employee Share',
        compute='_compute_shares',
        store=True,
        help="Amount to be paid by employee"
    )

    insurance_share = fields.Float(
        string='Insurance Share',
        compute='_compute_shares',
        store=True,
        help="Amount to be paid by insurance company"
    )

    deductible_applied = fields.Float(
        string='Deductible Applied',
        compute='_compute_shares',
        store=True,
        help="Deductible amount applied to this claim"
    )

    claim_status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ], string='Claim Status',
       default='draft',
       required=True,
       help="Current status of the claim"
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        help="Reason for claim rejection"
    )

    supporting_documents = fields.Binary(
        string='Supporting Documents',
        help="Supporting documents for the claim"
    )

    supporting_documents_filename = fields.Char(
        string='Supporting Documents Filename'
    )

    notes = fields.Text(
        string='Notes',
        help="Additional notes about the claim"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help="Company"
    )

    @api.depends('total_amount', 'approved_amount', 'insurance_plan_id.deductible_amount', 
                 'insurance_plan_id.co_payment_percentage')
    def _compute_shares(self):
        for claim in self:
            if claim.approved_amount > 0:
                # Apply deductible
                deductible_remaining = claim.insurance_plan_id.deductible_amount
                claim.deductible_applied = min(deductible_remaining, claim.approved_amount)
                amount_after_deductible = claim.approved_amount - claim.deductible_applied
                
                # Apply co-payment
                co_payment_amount = amount_after_deductible * (claim.insurance_plan_id.co_payment_percentage / 100)
                claim.employee_share = claim.deductible_applied + co_payment_amount
                claim.insurance_share = claim.approved_amount - claim.employee_share
            else:
                claim.employee_share = 0
                claim.insurance_share = 0
                claim.deductible_applied = 0

    @api.model
    def _generate_claim_reference(self):
        """Generate unique claim reference"""
        return f"MIC-{datetime.now().strftime('%Y%m%d')}-{self.env['ir.sequence'].next_by_code('medical.insurance.claim') or '0001'}"

    @api.constrains('treatment_date', 'claim_date')
    def _check_dates(self):
        for claim in self:
            if claim.treatment_date > claim.claim_date:
                raise ValueError("Treatment date cannot be after claim date")

    @api.constrains('total_amount')
    def _check_total_amount(self):
        for claim in self:
            if claim.total_amount <= 0:
                raise ValueError("Total amount must be greater than 0")

    def action_submit(self):
        """Submit claim for review"""
        self.write({'claim_status': 'submitted'})

    def action_approve(self):
        """Approve the claim"""
        if not self.approved_amount:
            self.approved_amount = self.total_amount
        self.write({'claim_status': 'approved'})

    def action_reject(self):
        """Reject the claim"""
        if not self.rejection_reason:
            raise ValueError("Please provide a rejection reason")
        self.write({'claim_status': 'rejected'})

    def action_process(self):
        """Process the claim for payment"""
        if self.claim_status != 'approved':
            raise ValueError("Only approved claims can be processed")
        self.write({'claim_status': 'processed'})

    def action_reset_to_draft(self):
        """Reset claim to draft status"""
        self.write({'claim_status': 'draft'})

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Set insurance plan based on employee"""
        if self.employee_id and self.employee_id.medical_insurance_plan_id:
            self.insurance_plan_id = self.employee_id.medical_insurance_plan_id
