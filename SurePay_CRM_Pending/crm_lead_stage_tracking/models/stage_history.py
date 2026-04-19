from odoo import models, fields

class StageHistory(models.Model):
    _name = 'crm.lead.stage.history'
    _description = 'CRM Lead Stage History'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    stage_id = fields.Many2one('crm.stage', string='Stage', required=True)
    entered_date = fields.Datetime(string='Entered Date', required=True)
    exited_date = fields.Datetime(string='Exited Date')