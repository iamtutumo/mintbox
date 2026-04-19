from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    visit_count = fields.Integer('Visits', compute='_compute_visit_count')
    visit_ids = fields.One2many('surepay.client.visit', 'lead_id', 'Visits')

    def _compute_visit_count(self):
        try:
            visit_data = self.env['surepay.client.visit'].read_group(
                [('lead_id', 'in', self.ids)],
                ['lead_id'],
                ['lead_id']
            )
            mapped_data = {data['lead_id'][0]: data['lead_id_count'] for data in visit_data}
            for lead in self:
                lead.visit_count = mapped_data.get(lead.id, 0)
        except Exception as e:
            # If there's an access error, set visit count to 0
            for lead in self:
                lead.visit_count = 0
            # Log the error for debugging
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Access error in crm_lead _compute_visit_count: {e}")

    def action_view_visits(self):
        """
        Action to open the list of visits for this lead.
        """
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('surepay_client_visits.action_client_visit')
        action['domain'] = [('lead_id', '=', self.id)]
        action['context'] = {
            'default_lead_id': self.id,
            'default_partner_id': self.partner_id.id,
            'search_default_group_by_visit_date': 1,
        }
        return action
        
    def action_log_visit(self):
        """
        Action to quickly log a new visit for this lead.
        """
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('surepay_client_visits.action_client_visit')
        action['views'] = [(False, 'form')]
        action['context'] = {
            'default_lead_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_visit_date': fields.Datetime.now(),
            'default_user_id': self.env.uid,
        }
        return action
