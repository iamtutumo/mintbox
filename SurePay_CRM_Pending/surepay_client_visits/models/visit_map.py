from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class VisitMap(models.TransientModel):
    _name = 'surepay.visit.map'
    _description = 'Visit Map Dashboard'
    _order = 'create_date desc'

    # Filter fields
    date_from = fields.Datetime('Date From', default=lambda self: fields.Datetime.now() - relativedelta(weeks=1))
    date_to = fields.Datetime('Date To', default=lambda self: fields.Datetime.now())
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Client', domain="[('is_company', '=', True)]")
    purpose = fields.Selection([
        ('intro', 'Introduction'),
        ('follow-up', 'Follow-up'),
        ('demo', 'Product Demo'),
        ('kyc', 'KYC'),
        ('closing', 'Closing'),
        ('support', 'Support'),
        ('other', 'Other')
    ], string='Purpose')
    
    # Computed fields for statistics
    visit_count = fields.Integer('Total Visits', compute='_compute_statistics')
    unique_clients = fields.Integer('Unique Clients', compute='_compute_statistics')
    avg_visits_per_day = fields.Float('Avg Visits/Day', compute='_compute_statistics', digits=(10, 2))
    
    # Related fields for map display
    visit_ids = fields.Many2many('surepay.client.visit', string='Visits', compute='_compute_visits')
    map_center_lat = fields.Float('Map Center Latitude', compute='_compute_map_center')
    map_center_lon = fields.Float('Map Center Longitude', compute='_compute_map_center')
    map_zoom = fields.Integer('Map Zoom Level', default=10)

    @api.depends('date_from', 'date_to', 'user_id', 'partner_id', 'purpose')
    def _compute_visits(self):
        for record in self:
            domain = [
                ('visit_date', '>=', record.date_from),
                ('visit_date', '<=', record.date_to),
                ('latitude', '!=', False),
                ('longitude', '!=', False),
            ]
            
            if record.user_id:
                domain.append(('user_id', '=', record.user_id.id))
            if record.partner_id:
                domain.append(('partner_id', '=', record.partner_id.id))
            if record.purpose:
                domain.append(('purpose', '=', record.purpose))
            
            try:
                visits = self.env['surepay.client.visit'].search(domain)
                record.visit_ids = visits
            except Exception as e:
                # If there's an access error, set empty visits
                record.visit_ids = self.env['surepay.client.visit']
                # Log the error for debugging
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Access error in _compute_visits: {e}")

    @api.depends('visit_ids')
    def _compute_statistics(self):
        for record in self:
            try:
                visits = record.visit_ids
                record.visit_count = len(visits)
                
                # Count unique clients
                unique_partners = visits.mapped('partner_id')
                record.unique_clients = len(unique_partners)
                
                # Calculate average visits per day
                if record.date_from and record.date_to:
                    days_diff = (record.date_to - record.date_from).days + 1
                    if days_diff > 0:
                        record.avg_visits_per_day = record.visit_count / days_diff
                    else:
                        record.avg_visits_per_day = 0
                else:
                    record.avg_visits_per_day = 0
            except Exception as e:
                # If there's an error, set default values
                record.visit_count = 0
                record.unique_clients = 0
                record.avg_visits_per_day = 0
                # Log the error for debugging
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Access error in _compute_statistics: {e}")

    @api.depends('visit_ids')
    def _compute_map_center(self):
        for record in self:
            try:
                visits = record.visit_ids.filtered(lambda v: v.latitude and v.longitude)
                if visits:
                    # Calculate center point (average of all coordinates)
                    avg_lat = sum(visits.mapped('latitude')) / len(visits)
                    avg_lon = sum(visits.mapped('longitude')) / len(visits)
                    record.map_center_lat = avg_lat
                    record.map_center_lon = avg_lon
                else:
                    # Default to center of Kenya (Nairobi)
                    record.map_center_lat = -1.2921
                    record.map_center_lon = 36.8219
            except Exception as e:
                # If there's an error, set default coordinates
                record.map_center_lat = -1.2921
                record.map_center_lon = 36.8219
                # Log the error for debugging
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Access error in _compute_map_center: {e}")

    def action_view_calendar(self):
        """Open calendar view with current filters"""
        self.ensure_one()
        
        domain = [
            ('visit_date', '>=', self.date_from),
            ('visit_date', '<=', self.date_to),
        ]
        
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.purpose:
            domain.append(('purpose', '=', self.purpose))
        
        return {
            'name': _('Visit Calendar'),
            'type': 'ir.actions.act_window',
            'res_model': 'surepay.client.visit',
            'view_mode': 'calendar',
            'domain': domain,
            'context': {
                'search_default_today': 1,
                'search_default_this_week': 1,
                'default_user_id': self.user_id.id if self.user_id else False,
            }
        }

    def action_view_list(self):
        """Open list view with current filters"""
        self.ensure_one()
        
        domain = [
            ('visit_date', '>=', self.date_from),
            ('visit_date', '<=', self.date_to),
        ]
        
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.purpose:
            domain.append(('purpose', '=', self.purpose))
        
        return {
            'name': _('Visit List'),
            'type': 'ir.actions.act_window',
            'res_model': 'surepay.client.visit',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {
                'search_default_today': 1,
                'search_default_this_week': 1,
                'default_user_id': self.user_id.id if self.user_id else False,
            }
        }

    def action_export_visits(self):
        """Export filtered visits to Excel"""
        self.ensure_one()
        
        domain = [
            ('visit_date', '>=', self.date_from),
            ('visit_date', '<=', self.date_to),
        ]
        
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.purpose:
            domain.append(('purpose', '=', self.purpose))
        
        visits = self.env['surepay.client.visit'].search(domain)
        
        if not visits:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Visits Found'),
                    'message': _('No visits found for the selected filters.'),
                    'type': 'warning',
                }
            }
        
        # Create Excel export
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/export/xls?model=surepay.client.visit&domain=' + str(domain),
            'target': 'self',
        }

    def action_set_this_week(self):
        """Set date range to current week"""
        today = fields.Date.today()
        start_of_week = today - relativedelta(days=today.weekday())
        end_of_week = start_of_week + relativedelta(days=6)
        
        self.write({
            'date_from': fields.Datetime.to_string(start_of_week) + ' 00:00:00',
            'date_to': fields.Datetime.to_string(end_of_week) + ' 23:59:59',
        })

    def action_set_this_month(self):
        """Set date range to current month"""
        today = fields.Date.today()
        start_of_month = today.replace(day=1)
        end_of_month = start_of_month + relativedelta(months=1, days=-1)
        
        self.write({
            'date_from': fields.Datetime.to_string(start_of_month) + ' 00:00:00',
            'date_to': fields.Datetime.to_string(end_of_month) + ' 23:59:59',
        })

    def action_set_last_week(self):
        """Set date range to last week"""
        today = fields.Date.today()
        start_of_last_week = today - relativedelta(days=today.weekday() + 7)
        end_of_last_week = start_of_last_week + relativedelta(days=6)
        
        self.write({
            'date_from': fields.Datetime.to_string(start_of_last_week) + ' 00:00:00',
            'date_to': fields.Datetime.to_string(end_of_last_week) + ' 23:59:59',
        })
