from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class ClientVisit(models.Model):
    _name = 'surepay.client.visit'
    _description = 'Client Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, id desc'

    name = fields.Char('Reference', required=True, default='New', copy=False, index=True)
    lead_id = fields.Many2one(
        'crm.lead', string='Opportunity', 
        domain="[('type', '=', 'opportunity')]"
    )
    partner_id = fields.Many2one(
        'res.partner', string='Client',
        required=True, tracking=True,
        domain="[('is_company', '=', True)]"
    )
    user_id = fields.Many2one(
        'res.users', string='Salesperson', 
        default=lambda self: self.env.user,
        required=True, tracking=True
    )
    visit_date = fields.Datetime(
        'Visit Date & Time', 
        default=fields.Datetime.now,
        required=True, tracking=True
    )
    purpose = fields.Selection([
        ('intro', 'Introduction'),
        ('follow-up', 'Follow-up'),
        ('demo', 'Product Demo'),
        ('kyc', 'KYC'),
        ('closing', 'Closing'),
        ('support', 'Support'),
        ('other', 'Other')
    ], string='Purpose', required=True, tracking=True)
    comments = fields.Text('Comments')
    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))
    temp_latitude = fields.Float('Temporary Latitude', digits=(10, 7), help='Temporary storage for coordinates before saving')
    temp_longitude = fields.Float('Temporary Longitude', digits=(10, 7), help='Temporary storage for coordinates before saving')
    map_url = fields.Char('Map URL', compute='_compute_map_url', store=False, readonly=True)
    map_iframe_url = fields.Char('Map Iframe URL', compute='_compute_map_url', store=False, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', 
        default=lambda self: self.env.company,
        required=True
    )

    @api.depends('latitude', 'longitude')
    def _compute_map_url(self):
        for visit in self:
            if visit.latitude and visit.longitude:
                bbox = f"{visit.longitude-0.01}%2C{visit.latitude-0.01}%2C{visit.longitude+0.01}%2C{visit.latitude+0.01}"
                marker = f"{visit.latitude}%2C{visit.longitude}"
                visit.map_iframe_url = f"https://www.openstreetmap.org/export/embed.html?bbox={bbox}&layer=mapnik&marker={marker}"
                visit.map_url = f"https://www.openstreetmap.org/?mlat={visit.latitude}&mlon={visit.longitude}#map=16/{visit.latitude}/{visit.longitude}"
            else:
                visit.map_iframe_url = False
                visit.map_url = False

    @api.model
    def create(self, vals):
        # Handle batch creation
        if isinstance(vals, list):
            # Batch create multiple records
            processed_vals = []
            for val in vals:
                # Copy temporary coordinates to actual coordinates if they exist
                temp_latitude = val.pop('temp_latitude', None)
                temp_longitude = val.pop('temp_longitude', None)
                
                # Check if actual coordinates are already provided
                actual_latitude = val.get('latitude')
                actual_longitude = val.get('longitude')
                
                # Use temporary coordinates if actual coordinates are not provided
                if temp_latitude is not None and temp_longitude is not None:
                    if actual_latitude is None and actual_longitude is None:
                        val['latitude'] = temp_latitude
                        val['longitude'] = temp_longitude
                        _logger.info(f'Using temporary coordinates for new visit: lat={temp_latitude}, lon={temp_longitude}')
                    else:
                        _logger.info(f'Temporary coordinates ignored, using actual coordinates: lat={actual_latitude}, lon={actual_longitude}')
                
                processed_vals.append(val)
            
            # Create all records at once
            results = super(ClientVisit, self).create(processed_vals)
            
            # Log the created visits and auto-generate names
            for result, val in zip(results, processed_vals):
                # Log the created visit with coordinates
                if result.latitude and result.longitude:
                    _logger.info(f'New visit created with coordinates: {result.id} - lat={result.latitude}, lon={result.longitude}')
                else:
                    _logger.info(f'New visit created without coordinates: {result.id}')
                
                # Auto-generate name if it's 'New'
                if result.name == 'New':
                    partner_id = val.get('partner_id')
                    visit_date = val.get('visit_date') or fields.Datetime.now()
                    
                    if partner_id:
                        partner = self.env['res.partner'].browse(partner_id)
                        if partner.exists():
                            date_str = fields.Datetime.to_string(visit_date)
                            if isinstance(visit_date, str):
                                # If it's already a string, parse it properly
                                from datetime import datetime
                                dt = datetime.fromisoformat(visit_date.replace('Z', '+00:00'))
                                date_str = dt.strftime('%Y-%m-%d %H:%M')
                            else:
                                # If it's a datetime object
                                date_str = visit_date.strftime('%Y-%m-%d %H:%M')
                            result.name = f"Visit to {partner.name} - {date_str}"
                        else:
                            result.name = self.env['ir.sequence'].next_by_code('surepay.client.visit') or 'New'
                    else:
                        result.name = self.env['ir.sequence'].next_by_code('surepay.client.visit') or 'New'
            
            return results
        else:
            # Single record creation
            # Copy temporary coordinates to actual coordinates if they exist
            temp_latitude = vals.pop('temp_latitude', None)
            temp_longitude = vals.pop('temp_longitude', None)
            
            # Check if actual coordinates are already provided
            actual_latitude = vals.get('latitude')
            actual_longitude = vals.get('longitude')
            
            # Use temporary coordinates if actual coordinates are not provided
            if temp_latitude is not None and temp_longitude is not None:
                if actual_latitude is None and actual_longitude is None:
                    vals['latitude'] = temp_latitude
                    vals['longitude'] = temp_longitude
                    _logger.info(f'Using temporary coordinates for new visit: lat={temp_latitude}, lon={temp_longitude}')
                else:
                    _logger.info(f'Temporary coordinates ignored, using actual coordinates: lat={actual_latitude}, lon={actual_longitude}')
            
            # Create the record first
            result = super(ClientVisit, self).create(vals)
            
            # Log the created visit with coordinates
            if result.latitude and result.longitude:
                _logger.info(f'New visit created with coordinates: {result.id} - lat={result.latitude}, lon={result.longitude}')
            else:
                _logger.info(f'New visit created without coordinates: {result.id}')
            
            # Auto-generate name if it's 'New'
            if result.name == 'New':
                partner_id = vals.get('partner_id')
                visit_date = vals.get('visit_date') or fields.Datetime.now()
                
                if partner_id:
                    partner = self.env['res.partner'].browse(partner_id)
                    if partner.exists():
                        date_str = fields.Datetime.to_string(visit_date)
                        if isinstance(visit_date, str):
                            # If it's already a string, parse it properly
                            from datetime import datetime
                            dt = datetime.fromisoformat(visit_date.replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d %H:%M')
                        else:
                            # If it's a datetime object
                            date_str = visit_date.strftime('%Y-%m-%d %H:%M')
                        result.name = f"Visit to {partner.name} - {date_str}"
                    else:
                        result.name = self.env['ir.sequence'].next_by_code('surepay.client.visit') or 'New'
                else:
                    result.name = self.env['ir.sequence'].next_by_code('surepay.client.visit') or 'New'
            
            return result
    
    @api.model
    def create_with_coordinates(self, vals, coordinates=None):
        """Create a new visit with optional coordinates.
        
        Args:
            vals (dict): Visit field values
            coordinates (dict, optional): Dictionary with 'latitude' and 'longitude' keys
        
        Returns:
            record: Created visit record
        """
        # Create the record
        visit = self.create(vals)
        
        # If coordinates are provided, update the record
        if coordinates and coordinates.get('latitude') and coordinates.get('longitude'):
            try:
                visit.write({
                    'latitude': coordinates['latitude'],
                    'longitude': coordinates['longitude'],
                })
                _logger.info(f'Coordinates saved for new visit {visit.id}: {coordinates["latitude"]}, {coordinates["longitude"]}')
            except Exception as e:
                _logger.error(f'Failed to save coordinates for visit {visit.id}: {e}')
        
        return visit
    
    def write(self, vals):
        """Override write to control coordinate modifications."""
        # Check if coordinates are being updated
        latitude = vals.get('latitude')
        longitude = vals.get('longitude')
        
        if latitude is not None or longitude is not None:
            # Allow coordinate updates only if:
            # 1. Coming from location capture (context flag)
            # 2. User is admin
            # 3. No existing coordinates (first time setting)
            from_location_capture = self.env.context.get('from_location_capture', False)
            is_admin = self.env.user.has_group('base.group_system')
            
            # Check if any record already has coordinates
            has_existing_coords = any(visit.latitude and visit.longitude for visit in self)
            
            if not (from_location_capture or is_admin or not has_existing_coords):
                _logger.warning(f'Unauthorized coordinate update attempt by user {self.env.user.name}')
                raise UserError(_('You cannot manually update coordinates. Please use the "Capture Current Location" button.'))
            
            _logger.info(f'Coordinates being updated: lat={latitude}, lon={longitude}, from_capture={from_location_capture}, admin={is_admin}')
        
        # Call super write method
        result = super(ClientVisit, self).write(vals)
        
        # Log successful coordinate updates
        if latitude is not None or longitude is not None:
            for visit in self:
                _logger.info(f'Visit {visit.id} coordinates updated: lat={visit.latitude}, lon={visit.longitude}')
        
        return result

    @api.onchange('partner_id', 'visit_date')
    def _onchange_partner_or_date(self):
        """Auto-update name when partner or visit date changes."""
        if self.partner_id and self.visit_date:
            # Format: Visit to [Client Name] - [Date]
            if isinstance(self.visit_date, str):
                # If it's already a string, parse it properly
                from datetime import datetime
                dt = datetime.fromisoformat(self.visit_date.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d %H:%M')
            else:
                # If it's a datetime object
                date_str = self.visit_date.strftime('%Y-%m-%d %H:%M')
            self.name = f"Visit to {self.partner_id.name} - {date_str}"
        elif self.partner_id:
            # If only partner is selected, use current date
            date_str = fields.Datetime.now().strftime('%Y-%m-%d %H:%M')
            self.name = f"Visit to {self.partner_id.name} - {date_str}"
        else:
            # Reset to default if no partner
            self.name = 'New'

    def action_open_map(self):
        """Open the location in the default map application."""
        self.ensure_one()
        if not self.map_url:
            raise UserError(_('No location data available for this visit.'))
        return {
            'type': 'ir.actions.act_url',
            'url': self.map_url,
            'target': 'new',
        }

    def open_lead(self):
        """Open the related lead/opportunity."""
        self.ensure_one()
        if not self.lead_id:
            raise UserError(_('No opportunity is linked to this visit.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': self.lead_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_capture_location(self):
        """Action to trigger location capture via client-side JavaScript."""
        return {
            'type': 'ir.actions.client',
            'tag': 'surepay_client_visits.capture_location',
            'params': {
                'model': self._name,
                'res_id': self.id,
                'update_map': True,
            },
        }


    @api.model
    def create_visit_from_partner(self, partner_id, lead_id=None):
        """Create a new visit from partner or lead.
        
        Args:
            partner_id (int): ID of the partner
            lead_id (int, optional): ID of the related lead/opportunity
        """
        visit_vals = {
            'partner_id': partner_id,
            'visit_date': fields.Datetime.now(),
            'user_id': self.env.uid,
        }
        if lead_id:
            visit_vals['lead_id'] = lead_id
        return self.create(visit_vals)

    def open_partner(self):
        """Open the related client/partner."""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_('No client is linked to this visit.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('lead_id')
    def _onchange_lead_id(self):
        if self.lead_id and self.lead_id.partner_id:
            self.partner_id = self.lead_id.partner_id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and not self.lead_id:
            return {'domain': {
                'lead_id': [('partner_id', '=', self.partner_id.id), ('type', '=', 'opportunity')]
            }}

    @api.model
    def update_existing_records_coordinates(self):
        """Update existing records to populate coordinate fields properly.
        
        This method checks existing records and updates their coordinates
        based on various sources:
        1. Temporary coordinate fields (if they have values)
        2. Partner address coordinates (if available)
        3. Company address coordinates (as fallback)
        
        Returns:
            dict: Summary of updates made
        """
        _logger.info('Starting coordinate update for existing client visit records')
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        # Get all existing records
        visits = self.search([])
        _logger.info(f'Found {len(visits)} client visit records to process')
        
        for visit in visits:
            try:
                # Skip records that already have valid coordinates
                if visit.latitude and visit.longitude and visit.latitude != 0.0 and visit.longitude != 0.0:
                    _logger.debug(f'Skipping visit {visit.id} - already has valid coordinates: {visit.latitude}, {visit.longitude}')
                    skipped_count += 1
                    continue
                
                new_latitude = None
                new_longitude = None
                source = None
                
                # Check if temporary fields have values (for records that were created but not saved properly)
                if visit.temp_latitude and visit.temp_longitude and visit.temp_latitude != 0.0 and visit.temp_longitude != 0.0:
                    new_latitude = visit.temp_latitude
                    new_longitude = visit.temp_longitude
                    source = 'temporary_fields'
                    _logger.info(f'Found coordinates in temporary fields for visit {visit.id}: {new_latitude}, {new_longitude}')
                
                # If no temp coordinates, try to get from partner address
                elif visit.partner_id and visit.partner_id.partner_latitude and visit.partner_id.partner_longitude:
                    new_latitude = visit.partner_id.partner_latitude
                    new_longitude = visit.partner_id.partner_longitude
                    source = 'partner_address'
                    _logger.info(f'Using partner coordinates for visit {visit.id}: {new_latitude}, {new_longitude}')
                
                # If no partner coordinates, try company address as fallback
                elif visit.company_id:
                    # Check if company has coordinate fields (they might be named differently)
                    company_lat = getattr(visit.company_id, 'partner_latitude', None) or getattr(visit.company_id, 'latitude', None)
                    company_lon = getattr(visit.company_id, 'partner_longitude', None) or getattr(visit.company_id, 'longitude', None)
                    if company_lat and company_lon and company_lat != 0.0 and company_lon != 0.0:
                        new_latitude = company_lat
                        new_longitude = company_lon
                        source = 'company_address'
                        _logger.info(f'Using company coordinates for visit {visit.id}: {new_latitude}, {new_longitude}')
                
                # If no coordinates found yet, use default coordinates as last resort
                if not new_latitude or not new_longitude:
                    # Use default coordinates (Kampala city center, Uganda)
                    # More precise coordinates for Kampala Central Business District
                    new_latitude = 0.3177  # Kampala CBD, Uganda
                    new_longitude = 32.5822
                    source = 'default_coordinates'
                    _logger.info(f'Using default coordinates for visit {visit.id}: {new_latitude}, {new_longitude}')
                
                # If we found coordinates, update the record
                if new_latitude and new_longitude:
                    # Use write with system context to bypass coordinate restrictions
                    visit.with_context(from_location_capture=True).write({
                        'latitude': new_latitude,
                        'longitude': new_longitude,
                        'temp_latitude': False,  # Clear temporary fields after copying
                        'temp_longitude': False,
                    })
                    updated_count += 1
                    _logger.info(f'Updated visit {visit.id} with coordinates from {source}: {new_latitude}, {new_longitude}')
                else:
                    _logger.debug(f'No coordinates found for visit {visit.id}')
                    skipped_count += 1
                    
            except Exception as e:
                error_count += 1
                _logger.error(f'Error updating coordinates for visit {visit.id}: {e}')
        
        result = {
            'total_records': len(visits),
            'updated_records': updated_count,
            'skipped_records': skipped_count,
            'error_count': error_count,
            'message': f'Coordinate update completed. Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}'
        }
        
        _logger.info(f'Coordinate update summary: {result}')
        return result

