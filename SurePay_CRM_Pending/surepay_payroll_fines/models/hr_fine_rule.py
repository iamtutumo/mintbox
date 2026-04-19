from odoo import models, fields, api

class HrFineRule(models.Model):
    _name = 'hr.fine.rule'
    _description = 'HR Fine Rule'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help="Name of the fine rule"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        help="Unique code for the fine rule"
    )
    
    description = fields.Text(
        string='Description',
        help="Description of when this fine applies"
    )
    
    default_amount = fields.Float(
        string='Default Amount',
        required=True,
        help="Default fine amount"
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether this fine rule is active"
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help="Company this rule applies to"
    )
    
    fine_ids = fields.One2many(
        'hr.fine', 'fine_rule_id',
        string='Fines',
        help="Fines created using this rule"
    )
    
    _sql_constraints = [
        ('code_uniq', 'unique(code, company_id)', 'Fine rule code must be unique per company!'),
    ]
    
    @api.model
    def _get_default_fine_rules(self):
        """Create default fine rules"""
        default_rules = [
            {
                'name': 'Late Arrival',
                'code': 'LATE_ARRIVAL',
                'description': 'Fine for arriving late to work',
                'default_amount': 5000.0,
            },
            {
                'name': 'Unauthorized Absence',
                'code': 'UNAUTHORIZED_ABSENCE',
                'description': 'Fine for unauthorized absence from work',
                'default_amount': 15000.0,
            },
            {
                'name': 'Uniform Violation',
                'code': 'UNIFORM_VIOLATION',
                'description': 'Fine for not wearing proper uniform',
                'default_amount': 3000.0,
            },
            {
                'name': 'Safety Violation',
                'code': 'SAFETY_VIOLATION',
                'description': 'Fine for violating safety procedures',
                'default_amount': 10000.0,
            },
        ]
        
        for rule_data in default_rules:
            existing_rule = self.search([
                ('code', '=', rule_data['code']),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            if not existing_rule:
                self.create(rule_data)
