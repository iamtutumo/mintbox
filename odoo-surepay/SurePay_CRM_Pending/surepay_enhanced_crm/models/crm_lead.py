from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Product Interest Selection
    product_interest = fields.Selection([
        ('sims', 'SIMS'),
        ('surebanker', 'SureBanker'),
        ('other', 'Other')
    ], string='Product Interest', tracking=True)

    # Common Fields
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority', default='medium')
    source = fields.Char(string='Source of Lead')
    location = fields.Char(string='Location')
    expected_closing_date = fields.Date(string='Expected Closing Date')
    additional_info = fields.Text(string='Additional Information')

    # SIMS Specific Fields
    number_of_students = fields.Integer(string='Number of Students')
    school_code = fields.Char(string='School Code')

    # SureBanker Specific Fields
    number_of_members = fields.Integer(string='Number of Members')
    number_of_branches = fields.Integer(string='Number of Branches')
    package = fields.Selection([
        ('bronze', 'Bronze - 400k/month'),
        ('silver', 'Silver - 800k/month'),
        ('gold', 'Gold - 1.2M/month'),
        ('platinum', 'Platinum - 1.6M/month')
    ], string='Package')
    sacco_id = fields.Char(string='SACCO ID')

    # Lost/Cold Lead Reasons
    reason_for_loss = fields.Text(string='Reason for Loss')
    reason_for_cold = fields.Text(string='Reason for Cold Lead')
    next_course_of_action = fields.Text(string='Recommended Next Course of Action')
    
    # Computed Fields
    expected_revenue = fields.Monetary(
        string='Expected Revenue',
        currency_field='company_currency',
        compute='_compute_expected_revenue',
        store=True
    )
    
    @api.depends('product_interest', 'number_of_students', 'package')
    def _compute_expected_revenue(self):
        package_prices = {
            'bronze': 400000,  # 400k
            'silver': 800000,  # 800k
            'gold': 1200000,   # 1.2M
            'platinum': 1600000  # 1.6M
        }

        for lead in self:
            revenue = 0.0
            if lead.product_interest == 'sims' and lead.number_of_students > 0:
                # (Number of students × 3 payments per term × 3 terms per year) ÷ 12 months
                revenue = (lead.number_of_students * 3 * 3) / 12
            elif lead.product_interest == 'surebanker' and lead.package:
                revenue = package_prices.get(lead.package, 0)
            # For other products, revenue remains 0
            lead.expected_revenue = revenue
    
    # Action Methods for Stage-Specific Forms
    def action_open_preparation_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lead Preparation',
            'res_model': 'crm.lead',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('surepay_enhanced_crm.crm_lead_preparation_form_view').id,
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }
    
    def action_open_closing_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lead Closing',
            'res_model': 'crm.lead',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('surepay_enhanced_crm.crm_lead_closing_form_view').id,
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }
    
    def action_open_lost_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mark as Lost',
            'res_model': 'crm.lead',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('surepay_enhanced_crm.crm_lead_lost_form_view').id,
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }
    
    def action_open_cold_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mark as Cold',
            'res_model': 'crm.lead',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('surepay_enhanced_crm.crm_lead_cold_form_view').id,
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_set_cold(self):
        self.ensure_one()
        # Set stage to cold lead
        cold_stage = self.env.ref('surepay_enhanced_crm.stage_lead_cold', raise_if_not_found=False)
        if cold_stage:
            self.stage_id = cold_stage
        # Set probability to 0 for cold leads
        self.probability = 0
        return True