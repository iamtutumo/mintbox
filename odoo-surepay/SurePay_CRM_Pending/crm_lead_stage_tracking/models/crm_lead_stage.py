from odoo import models, fields

class CrmLeadStage(models.Model):
    _inherit = 'crm.stage'

    allowed_duration_days = fields.Integer(string='Allowed Duration (Days)', default=7, help='Maximum days a lead can stay in this stage before notification')