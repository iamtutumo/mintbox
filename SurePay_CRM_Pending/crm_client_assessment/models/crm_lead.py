from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Partner Info Section
    organization_name = fields.Char(string="Organization Name")
    years_in_business = fields.Integer(string="Years in Business")
    sector_industry = fields.Char(string="Sector/Industry")
    contact_person = fields.Char(string="Contact Person")
    head_office_location = fields.Char(string="Head Office Location")
    project_coordinator_phone = fields.Char(string="Contact Number for the Project Coordinator")
    email_address = fields.Char(string="Email Address")
    skype_address = fields.Char(string="Skype Address")
    
    # Services Requested (Multi-select)
    services_requested = fields.Many2many(
        'crm.client.assessment.service',
        string="Services Requested",
        help="Select all services the client is interested in"
    )
    
    # Project Info
    main_expectation = fields.Text(string="Main Expectation from the SurePay Service Offer")
    current_transactions = fields.Text(string="Current Transactions",
                                     help="Description of current transactions")
    current_provider = fields.Char(string="Current Provider of the Service")
    current_average_transactions = fields.Float(string="Current Average of Transactions")
    average_transaction_value = fields.Float(string="Average Value of Each Transaction")
    
    # Projections
    estimated_customers = fields.Integer(string="Estimated Number of Customers Expected to Be Served")
    projected_transactions = fields.Text(string="Projected Transactions",
                                       help="Description of projected transactions")
    estimated_average_value = fields.Float(string="Estimated average Value of Each Transaction")
    expected_monthly_turnover = fields.Monetary(string="Expected Monthly Turnover",
                                              currency_field='company_currency')
    target_customers = fields.Text(string="Target Customers",
                                 help="Description of target customer segments")
    
    # Customer Distribution (Multi-select)
    customer_distribution = fields.Many2many(
        'crm.client.assessment.distribution',
        string="Customer Distribution",
        help="Select all applicable customer distribution channels"
    )
    
    # Onboarding
    onboarding_responsible_id = fields.Many2one(
        'res.users',
        string="Onboarding Responsible",
        tracking=True
    )
    marketing_budget = fields.Monetary(string="Marketing Budget",
                                     currency_field='company_currency')
    
    # Declaration
    declaration_date = fields.Date(string="Declaration Date",
                                 default=fields.Date.context_today)
    declaration_signature = fields.Binary(string="Signature")
    declaration_signed_by = fields.Char(string="Signed By")
    
    @api.constrains('email_address')
    def _check_email_address(self):
        """Validate email address format"""
        for record in self:
            if record.email_address:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.email_address):
                    raise models.ValidationError('Please enter a valid email address.')
    
    @api.constrains('project_coordinator_phone')
    def _check_phone_number(self):
        """Validate phone number format"""
        for record in self:
            if record.project_coordinator_phone:
                # Remove common phone number formatting characters
                phone_clean = ''.join(filter(str.isdigit, record.project_coordinator_phone))
                if len(phone_clean) < 10:
                    raise models.ValidationError('Please enter a valid phone number with at least 10 digits.')
    declaration_signed_on = fields.Datetime(string="Signed On")
