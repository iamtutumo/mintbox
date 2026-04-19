from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    visit_count = fields.Integer('Visits', compute='_compute_visit_count')
    visit_ids = fields.One2many('surepay.client.visit', 'partner_id', 'Visits')

    def _compute_visit_count(self):
        try:
            visit_data = self.env['surepay.client.visit'].read_group(
                [('partner_id', 'in', self.ids)],
                ['partner_id'],
                ['partner_id']
            )
            mapped_data = {data['partner_id'][0]: data['partner_id_count'] for data in visit_data}
            for partner in self:
                partner.visit_count = mapped_data.get(partner.id, 0)
        except Exception as e:
            # If there's an access error, set visit count to 0
            for partner in self:
                partner.visit_count = 0
            # Log the error for debugging
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Access error in res_partner _compute_visit_count: {e}")

    def action_view_visits(self):
        """
        Action to open the list of visits for this partner.
        """
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('surepay_client_visits.action_client_visit')
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {
            'default_partner_id': self.id,
            'search_default_group_by_visit_date': 1,
        }
        return action
        
    def action_log_visit(self):
        """
        Action to quickly log a new visit for this partner.
        """
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('surepay_client_visits.action_client_visit')
        action['views'] = [(False, 'form')]
        action['context'] = {
            'default_partner_id': self.id,
            'default_visit_date': fields.Datetime.now(),
            'default_user_id': self.env.uid,
        }
        return action
