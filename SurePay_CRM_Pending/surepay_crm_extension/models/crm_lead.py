from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re
import logging

_logger = logging.getLogger(__name__)

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    product_sync_code = fields.Char('Product Sync Code',
        help='Product synchronization code to be entered at Won stage')
    is_cold_lead = fields.Boolean('Is Cold Lead',
        help='Mark this lead as a cold lead')
    
    # Referral Fields
    is_referral = fields.Boolean('Is Referral',
        help='Mark this lead as coming from an external referral')
    referrer_name = fields.Char('Referrer Name',
        help='Name of the person who referred this lead')
    referrer_phone = fields.Char('Referrer Phone',
        help='Phone number of the person who referred this lead')
    referral_date = fields.Datetime('Referral Date',
        help='Date when the lead was referred', default=fields.Datetime.now)
    
    @api.model
    def create_lead_from_web_submission(self, submission_data):
        """
        Create a lead from web form submission
        """
        try:
            _logger.info(f"Creating lead from submission data: {submission_data}")
            
            # Validate required fields
            required_fields = ['contact_name', 'email_from', 'phone', 'referrer_name', 'referrer_phone']
            missing_fields = []
            
            for field in required_fields:
                if not submission_data.get(field):
                    missing_fields.append(field.replace('_', ' ').title())
            
            if missing_fields:
                missing_fields_str = ', '.join(missing_fields)
                error_msg = f"The following fields are required: {missing_fields_str}"
                _logger.error(f"Validation failed: {error_msg}")
                raise ValidationError(_(error_msg))
            
            # Create lead vals
            lead_vals = {
                'name': submission_data.get('name', f"Referral: {submission_data.get('contact_name')}"),
                'contact_name': submission_data.get('contact_name'),
                'email_from': submission_data.get('email_from'),
                'phone': submission_data.get('phone'),
                'mobile': submission_data.get('mobile'),
                'partner_name': submission_data.get('company_name'),
                'description': submission_data.get('description', ''),
                'type': 'lead',
                'is_referral': True,
                'referrer_name': submission_data.get('referrer_name'),
                'referrer_phone': submission_data.get('referrer_phone'),
                'referral_date': fields.Datetime.now(),
            }
            
            _logger.info(f"Lead values prepared: {lead_vals}")
            
            # Create the lead
            lead = self.create(lead_vals)
            _logger.info(f"Lead created successfully with ID: {lead.id}")
            
            return {
                'success': True,
                'lead_id': lead.id,
                'message': 'Lead created successfully'
            }
            
        except ValidationError as e:
            _logger.error(f"Validation error creating lead: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Error creating lead from web submission: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Error creating lead: {str(e)}"
            }

    @api.constrains('email_from')
    def _check_email_format(self):
        """Validate email format if provided"""
        for lead in self:
            if lead.email_from:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, lead.email_from):
                    raise ValidationError(_('Please enter a valid email address.'))

    def _normalize_phone_number(self, phone):
        """Normalize phone number by removing all non-digit characters"""
        if not phone:
            return ''
        # Remove all non-digit characters
        return ''.join(filter(str.isdigit, str(phone)))
        
    @api.constrains('phone', 'mobile')
    def _check_phone_numbers(self):
        """Check phone number constraints"""
        for lead in self:
            if lead.phone:
                lead.phone = self._normalize_phone_number(lead.phone)
            if lead.mobile:
                lead.mobile = self._normalize_phone_number(lead.mobile)

    def _check_duplicate_phone(self):
        """Check for duplicate phone numbers with flexible matching"""
        try:
            for lead in self:
                # Skip validation if no phone numbers are provided
                if not lead.phone and not lead.mobile:
                    continue
                    
                try:
                    # Normalize the phone numbers
                    lead_phone_norm = self._normalize_phone_number(lead.phone)
                    lead_mobile_norm = self._normalize_phone_number(lead.mobile)
                except Exception as e:
                    _logger.warning("Error normalizing phone numbers: %s", str(e))
                    continue
                
                if not lead_phone_norm and not lead_mobile_norm:
                    continue
                    
                # Build domain for search
                domain = []
                if lead_phone_norm:
                    domain.append(('phone', '!=', False))
                if lead_mobile_norm:
                    domain.append(('mobile', '!=', False))
                
                if lead.id:  # For existing records, exclude self
                    domain.append(('id', '!=', lead.id))
                    
                try:
                    # Search for potential duplicates
                    potential_duplicates = self.env['crm.lead'].search(domain)
                except Exception as e:
                    _logger.warning("Error searching for duplicate leads: %s", str(e))
                    continue
                
                # Check for matches with normalized numbers
                duplicate_leads = []
                for dup in potential_duplicates:
                    try:
                        dup_phone_norm = self._normalize_phone_number(dup.phone)
                        dup_mobile_norm = self._normalize_phone_number(dup.mobile)
                        
                        # Check if any normalized number matches
                        if ((lead_phone_norm and (lead_phone_norm == dup_phone_norm or 
                                               lead_phone_norm == dup_mobile_norm)) or
                            (lead_mobile_norm and (lead_mobile_norm == dup_phone_norm or 
                                               lead_mobile_norm == dup_mobile_norm))):
                            duplicate_leads.append(dup)
                    except Exception as e:
                        _logger.warning("Error processing duplicate lead %s: %s", dup.id, str(e))
                        continue
                
                if duplicate_leads:
                    duplicate_info = []
                    for dup_lead in duplicate_leads[:5]:  # Show first 5 duplicates
                        try:
                            partner_name = dup_lead.partner_name or dup_lead.contact_name or 'Unknown'
                            stage_name = dup_lead.stage_id.name if dup_lead.stage_id else 'Unknown'
                            duplicate_info.append(f"• {partner_name} (Stage: {stage_name})")
                        except Exception as e:
                            _logger.warning("Error formatting duplicate lead info: %s", str(e))
                            continue
                    
                    if duplicate_info:
                        duplicate_text = '\n'.join(duplicate_info)
                        raise ValidationError(_(
                            "A lead already exists with this phone number.\n\n"
                            f"{duplicate_text}" + "\n\n"
                            "Please check if you want to:\n"
                            "1. Update the existing lead instead of creating a new one\n"
                            "2. Use a different phone number for this new lead"
                        ))
        except ValidationError:
            # Re-raise ValidationError as is
            raise
        except Exception as e:
            # Log unexpected errors but don't block the operation
            _logger.error("Unexpected error in _check_duplicate_phone: %s", str(e))
            # Optionally, you can uncomment the line below to see the error in the UI
            # raise ValidationError(_("An error occurred while checking for duplicate leads. Please try again."))

    @api.model
    def create(self, vals):
        """Override create to provide better duplicate phone number handling"""
        # Check for duplicates before creation
        phone = vals.get('phone')
        mobile = vals.get('mobile')
        
        if phone or mobile:
            if phone and mobile:
                # Both phone and mobile provided - check for duplicates in either field
                domain = ['|', ('phone', '=', phone), ('mobile', '=', mobile)]
            elif phone:
                # Only phone provided
                domain = [('phone', '=', phone)]
            elif mobile:
                # Only mobile provided
                domain = [('mobile', '=', mobile)]
            
            existing_leads = self.env['crm.lead'].search(domain)
            
            if existing_leads:
                # Format the duplicate information
                duplicate_info = []
                for dup_lead in existing_leads[:3]:  # Show first 3 duplicates
                    partner_name = dup_lead.partner_name or dup_lead.contact_name or 'Unknown'
                    stage_name = dup_lead.stage_id.name if dup_lead.stage_id else 'Unknown'
                    duplicate_info.append(f"• {partner_name} (Stage: {stage_name})")
                
                duplicate_text = '\n'.join(duplicate_info)
                warning_message = (
                    "Warning: Leads with similar phone numbers already exist:\n\n"
                    f"{duplicate_text}" + "\n\n"
                    "Consider if you should:\n"
                    "• Update an existing lead instead\n"
                    "• Continue with creating a new lead\n"
                    "• Use different contact information"
                )
                
                # Log the warning but don't prevent creation
                _logger.warning(f"Duplicate phone number detected: {warning_message}")
        
        return super().create(vals)

    def _validate_cold_lead_to_prospecting(self):
        """Validate Cold Lead to Prospecting stage transition"""
        _logger.info("_validate_cold_lead_to_prospecting called")
        _logger.info(f"Checking: name={bool(self.name)}, partner_id={bool(self.partner_id)}, contact_name={bool(self.contact_name)}, phone={bool(self.phone)}, mobile={bool(self.mobile)}")
        
        if not self.name:
            raise UserError("Lead name is required to move to Prospecting stage")
        if not self.partner_id:
            raise UserError("Customer selection is required to move to Prospecting stage")
        if not self.contact_name:
            raise UserError("Contact person name is required to move to Prospecting stage")
        if not self.phone and not self.mobile:
            raise UserError("Phone number or mobile number is required to move to Prospecting stage")
        
        _logger.info("_validate_cold_lead_to_prospecting passed")

    def _validate_prospecting_to_preparation(self):
        """Validate Prospecting to Preparation stage transition"""
        _logger.info("_validate_prospecting_to_preparation called")
        _logger.info(f"Checking: expected_revenue={self.expected_revenue}, date_deadline={self.date_deadline}, lead_line_ids={bool(self.lead_line_ids)}, partner_name={bool(self.partner_name)}, description={bool(self.description)}")
        
        if not self.expected_revenue or self.expected_revenue <= 0:
            raise UserError("Expected revenue must be greater than 0 to move to Preparation stage")
        if not self.date_deadline:
            raise UserError("Expected closing date is required to move to Preparation stage")
        if self.date_deadline and self.date_deadline < fields.Date.today():
            raise UserError("Expected closing date must be in the future")
        if not self.lead_line_ids:
            raise UserError("At least one product line is required to move to Preparation stage")
        
        # Basic client information validation
        if not self.partner_name:
            raise UserError("Partner name is required to move to Preparation stage")
        if not self.description:
            raise UserError("Lead description is required to move to Preparation stage")
        
        _logger.info("_validate_prospecting_to_preparation passed")

    def _validate_preparation_to_closing(self):
        """Validate Preparation to Closing stage transition"""
        _logger.info("_validate_preparation_to_closing called")
        _logger.info(f"Checking: probability={self.probability}, partner_name={bool(self.partner_name)}, description={bool(self.description)}, email={bool(self.email_from)}, phone={bool(self.phone)}, mobile={bool(self.mobile)}")
        
        if not self.probability or self.probability < 70:
            raise UserError("Probability must be at least 70% to move to Closing stage")
        
        # Validate product lines are complete
        for line in self.lead_line_ids:
            if not line.product_id or not line.price_unit or not line.product_qty:
                raise UserError("All product lines must have complete product, price, and quantity information")
        
        # Basic lead information validation
        if not self.partner_name:
            raise UserError("Partner name is required to move to Closing stage")
        if not self.description:
            raise UserError("Lead description is required to move to Closing stage")
        if not self.email_from and not self.phone and not self.mobile:
            raise UserError("At least one contact method (email, phone, or mobile) is required to move to Closing stage")
        
        _logger.info("_validate_preparation_to_closing passed")

    def _validate_closing_to_won(self):
        """Validate Closing to Won stage transition"""
        _logger.info("_validate_closing_to_won called")
        _logger.info(f"Checking: probability={self.probability}, expected_revenue={self.expected_revenue}, is_cold_lead={self.is_cold_lead}, product_sync_code={bool(self.product_sync_code)}, partner_name={bool(self.partner_name)}, description={bool(self.description)}")
        
        if not self.probability or self.probability != 100:
            raise UserError("Probability must be 100% to mark as Won")
        if not self.expected_revenue or self.expected_revenue <= 0:
            raise UserError("Expected revenue must be finalized to mark as Won")
        
        # Product sync code validation
        if self.is_cold_lead and not self.product_sync_code:
            raise UserError("Product synchronization code is required for cold leads to mark as Won")
        
        # Validate all product lines are complete
        for line in self.lead_line_ids:
            if not line.product_id or not line.price_unit or not line.product_qty:
                raise UserError("All product lines must have complete information to mark as Won")
        
        # Final validation of basic information
        if not self.partner_name:
            raise UserError("Partner name is required to mark as Won")
        if not self.description:
            raise UserError("Lead description is required to mark as Won")
        
        _logger.info("_validate_closing_to_won passed")

    def _validate_any_stage_to_lost(self):
        """Validate any stage to Lost stage transition"""
        _logger.info("_validate_any_stage_to_lost called")
        _logger.info(f"Checking: probability={self.probability}")
        
        if not self.probability or self.probability != 0:
            raise UserError("Probability must be 0% to mark as Lost")
        
        _logger.info("_validate_any_stage_to_lost passed")

    def write(self, vals):
        """
        Override write to handle stage changes with validation
        """
        # Get old stage info before calling super
        old_stage = self.stage_id
        old_stage_name = old_stage.name if old_stage else ''
        
        # Apply validation before stage change
        if 'stage_id' in vals:
            new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            new_stage_name = new_stage.name if new_stage else ''
            
            # Debug: Print stage information
            _logger.info(f"Stage transition: '{old_stage_name}' -> '{new_stage_name}'")
            
            # Apply validation based on stage transition
            if old_stage_name.strip() == 'Cold Lead' and new_stage_name.strip() == 'Prospecting':
                _logger.info("Validating Cold Lead to Prospecting")
                self._validate_cold_lead_to_prospecting()
            elif old_stage_name.strip() == 'Prospecting' and new_stage_name.strip() == 'Preparation':
                _logger.info("Validating Prospecting to Preparation")
                self._validate_prospecting_to_preparation()
            elif old_stage_name.strip() == 'Preparation' and new_stage_name.strip() == 'Closing':
                _logger.info("Validating Preparation to Closing")
                self._validate_preparation_to_closing()
            elif old_stage_name.strip() == 'Closing' and new_stage_name.strip() == 'Won':
                _logger.info("Validating Closing to Won")
                self._validate_closing_to_won()
            elif new_stage_name.strip() == 'Lost':
                _logger.info("Validating to Lost stage")
                self._validate_any_stage_to_lost()
            else:
                _logger.info(f"No validation for transition: '{old_stage_name}' -> '{new_stage_name}'")
        
        result = super().write(vals)
        return result

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """
        When stage is changed, provide warnings for missing requirements
        """
        if not self.stage_id:
            return
            
        stage_name = self.stage_id.name
        
        if stage_name == 'Prospecting':
            warnings = []
            if not self.name:
                warnings.append("Lead name is required")
            if not self.partner_id:
                warnings.append("Customer selection is required")
            if not self.contact_name:
                warnings.append("Contact person name is required")
            if not self.phone and not self.mobile:
                warnings.append("Phone number or mobile number is required")
            
            if warnings:
                return {
                    'warning': {
                        'title': 'Prospecting Stage Requirements',
                        'message': 'To move to Prospecting stage, please ensure: \n- ' + '\n- '.join(warnings)
                    }
                }
        
        elif stage_name == 'Preparation':
            warnings = []
            if not self.expected_revenue or self.expected_revenue <= 0:
                warnings.append("Expected revenue must be greater than 0")
            if not self.date_deadline:
                warnings.append("Expected closing date is required")
            if not self.lead_line_ids:
                warnings.append("At least one product line is required")
            
            if warnings:
                return {
                    'warning': {
                        'title': 'Preparation Stage Requirements',
                        'message': 'To move to Preparation stage, please ensure: \n- ' + '\n- '.join(warnings)
                    }
                }
        
        elif stage_name == 'Closing':
            warnings = []
            if not self.probability or self.probability < 70:
                warnings.append("Probability must be at least 70%")
            if not self.partner_name:
                warnings.append("Partner name is required")
            if not self.description:
                warnings.append("Lead description is required")
            
            if warnings:
                return {
                    'warning': {
                        'title': 'Closing Stage Requirements',
                        'message': 'To move to Closing stage, please ensure: \n- ' + '\n- '.join(warnings)
                    }
                }
        
        elif stage_name == 'Won':
            warnings = []
            if not self.probability or self.probability != 100:
                warnings.append("Probability must be 100%")
            if self.is_cold_lead and not self.product_sync_code:
                warnings.append("Product synchronization code is required for cold leads")
            
            if warnings:
                return {
                    'warning': {
                        'title': 'Won Stage Requirements',
                        'message': 'To mark as Won, please ensure: \n- ' + '\n- '.join(warnings)
                    }
                }
    
