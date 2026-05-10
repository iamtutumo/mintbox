# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import random
import string
from odoo.exceptions import ValidationError, UserError

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'
    _description = 'Job Applicant with Tracking'

    # Tracking Fields
    tracking_id = fields.Char(
        string='Tracking ID',
        readonly=True,
        index=True,
        copy=False,
        help='Unique tracking ID for the applicant'
    )

    public_application_url = fields.Char(
        string='Public Application URL',
        compute='_compute_public_application_url',
        store=True
    )

    status_history = fields.One2many(
        'applicant.status.history',
        'applicant_id',
        string='Status History'
    )

    last_status_update = fields.Datetime(string='Last Status Update', readonly=True)
    
    @api.depends('tracking_id')
    def _compute_public_application_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for applicant in self:
            if applicant.tracking_id:
                applicant.public_application_url = f"{base_url}/applicant/tracking/{applicant.tracking_id}"
            else:
                applicant.public_application_url = False

    @api.model
    def create(self, vals):
        if not vals.get('tracking_id'):
            vals['tracking_id'] = self._generate_tracking_id()

        applicant = super(HrApplicant, self).create(vals)

        # Create initial status history only if applicant was created successfully
        if applicant and applicant.id:
            try:
                self.env['applicant.status.history'].create({
                    'applicant_id': applicant.id,
                    'status': 'draft',
                    'message': _('Application created')
                })
            except Exception as e:
                # Log error but don't fail the applicant creation
                pass

        return applicant

    def _generate_tracking_id(self):
        """Generate a unique tracking ID in the format APP-XXXXXXXX"""
        prefix = "APP-"
        charset = string.ascii_uppercase + string.digits

        while True:
            random_part = ''.join(random.choices(charset, k=8))
            tracking_id = f"{prefix}{random_part}"

            if not self.env['hr.applicant'].sudo().search([('tracking_id', '=', tracking_id)], limit=1):
                return tracking_id

    def action_send_tracking_link(self):
        """Action to send tracking link to applicant"""
        self.ensure_one()
        if not self.email_from:
            raise UserError(_("No email address provided for the applicant."))

        template = self.env.ref('hr_applicant_tracking_random.email_applicant_tracking_link', False)
        if template:
            template.send_mail(self.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Tracking link has been sent to the applicant.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        """Override write to track stage changes"""
        result = super(HrApplicant, self).write(vals)
        
        # Only create status history if stage_id changed and record is saved
        if 'stage_id' in vals:
            for applicant in self:
                if applicant.id and applicant.stage_id:
                    # Map hr.applicant stages to our status history stages
                    stage_mapping = {
                        'new': 'draft',
                        'initial_qualification': 'in_progress',
                        'contacted': 'in_progress',
                        'interviewed': 'interview',
                        'hired': 'hired',
                        'refused': 'rejected',
                        'archived': 'rejected'
                    }
                    status = stage_mapping.get(applicant.stage_id.sequence, 'in_progress')
                    
                    try:
                        # Create status history entry
                        self.env['applicant.status.history'].create({
                            'applicant_id': applicant.id,
                            'status': status,
                            'message': f'Stage changed to {applicant.stage_id.name}'
                        })
                        
                        # Update last status update
                        applicant.last_status_update = fields.Datetime.now()
                    except Exception:
                        pass
        
        return result

    def generate_missing_tracking_ids(self):
        """Generate tracking IDs for applicants that don't have one"""
        applicants_without_tracking = self.search([('tracking_id', '=', False)])
        for applicant in applicants_without_tracking:
            applicant.tracking_id = self._generate_tracking_id()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s tracking IDs generated.') % len(applicants_without_tracking),
                'type': 'success',
                'sticky': False,
            }
        }
