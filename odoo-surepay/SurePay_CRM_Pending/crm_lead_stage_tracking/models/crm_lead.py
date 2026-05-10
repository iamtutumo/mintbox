from odoo import models, fields, api
from datetime import datetime

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    stage_history_ids = fields.One2many('crm.lead.stage.history', 'lead_id', string='Stage History')
    days_in_stage = fields.Integer(string='Days in Stage', compute='_compute_days_in_stage', store=False)

    @api.depends('stage_history_ids', 'stage_id')
    def _compute_days_in_stage(self):
        for lead in self:
            if lead.stage_history_ids:
                current_history = lead.stage_history_ids.filtered(lambda h: not h.exited_date)
                if current_history:
                    entered = current_history.entered_date
                    if entered:
                        delta = datetime.now() - entered.replace(tzinfo=None)
                        lead.days_in_stage = delta.days
                    else:
                        lead.days_in_stage = 0
                else:
                    lead.days_in_stage = 0
            else:
                lead.days_in_stage = 0

    @api.model
    def create(self, vals):
        # Handle batch creation
        if isinstance(vals, list):
            # Batch create multiple records
            leads = super(CrmLead, self).create(vals)
            
            # Create stage history for each lead
            history_vals = []
            for lead in leads:
                if lead.stage_id:
                    history_vals.append({
                        'lead_id': lead.id,
                        'stage_id': lead.stage_id.id,
                        'entered_date': datetime.now(),
                    })
            
            # Create all history records at once
            if history_vals:
                self.env['crm.lead.stage.history'].create(history_vals)
            
            return leads
        else:
            # Single record creation
            lead = super(CrmLead, self).create(vals)
            if lead.stage_id:
                self.env['crm.lead.stage.history'].create({
                    'lead_id': lead.id,
                    'stage_id': lead.stage_id.id,
                    'entered_date': datetime.now(),
                })
            return lead

    def write(self, vals):
        if 'stage_id' in vals:
            new_stage_id = vals['stage_id']
            for lead in self:
                if lead.stage_id and lead.stage_history_ids:
                    # Update exited_date for current stage
                    current_history = lead.stage_history_ids.filtered(lambda h: not h.exited_date)
                    if current_history:
                        current_history.exited_date = datetime.now()
                # Create new history entry
                if new_stage_id:
                    self.env['crm.lead.stage.history'].create({
                        'lead_id': lead.id,
                        'stage_id': new_stage_id,
                        'entered_date': datetime.now(),
                    })
        return super(CrmLead, self).write(vals)

    def _check_overstaying_leads(self):
        """Scheduled method to check for overstaying leads and send notifications"""
        overstaying_leads = self.search([]).filtered(
            lambda lead: lead.days_in_stage > (lead.stage_id.allowed_duration_days or 7)
        )
        if overstaying_leads:
            # Get HR/CRM Managers
            manager_group = self.env.ref('crm.group_crm_manager')
            managers = manager_group.users
            if not managers:
                return
            # Send email
            template = self.env.ref('crm_lead_stage_tracking.email_template_overstaying_leads')
            template.send_mail(overstaying_leads[0].id, email_values={'email_to': ','.join(managers.mapped('email'))})