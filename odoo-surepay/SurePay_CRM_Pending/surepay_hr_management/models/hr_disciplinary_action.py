from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
import base64


class HrDisciplinaryAction(models.Model):
    _name = 'hr.disciplinary.action'
    _description = 'HR Disciplinary Action'
    _order = 'date desc'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    action_type = fields.Selection([
        ('warning', 'Warning'),
        ('written_warning', 'Written Warning'),
        ('suspension', 'Suspension'),
        ('demotion', 'Demotion'),
        ('termination', 'Termination'),
        ('other', 'Other')
    ], string='Action Type', required=True)
    
    date = fields.Date(string='Date', required=True, default=fields.Date.today())
    title = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description', required=True)
    notes = fields.Text(string='Additional Notes')
    
    # Impact Fields
    affects_salary_advance = fields.Boolean(string='Affects Salary Advance Eligibility',
                                          default=True,
                                          help='If checked, employee cannot request salary advance')
    affects_probation = fields.Boolean(string='Affects Probation Period',
                                     default=False,
                                     help='If checked, employee probation period is extended')
    probation_extension_days = fields.Integer(string='Probation Extension (Days)',
                                            default=0,
                                            help='Number of days to extend probation period')
    
    # Status Fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True)
    
    active = fields.Boolean(string='Active', default=True,
                           help='Whether this disciplinary action is currently active')
    resolution_date = fields.Date(string='Resolution Date')
    resolution_notes = fields.Text(string='Resolution Notes')
    
    # Attachment Fields
    attachment_ids = fields.Many2many('ir.attachment', 'disciplinary_action_attachment_rel',
                                    'disciplinary_action_id', 'attachment_id',
                                    string='Attachments')
    attachment_count = fields.Integer(string='Attachment Count',
                                    compute='_compute_attachment_count')
    
    # Approval Fields
    confirmed_by = fields.Many2one('res.users', string='Confirmed By')
    confirmed_date = fields.Datetime(string='Confirmed Date')
    
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for action in self:
            action.attachment_count = len(action.attachment_ids)
    
    @api.constrains('probation_extension_days')
    def _check_probation_extension_days(self):
        for action in self:
            if action.probation_extension_days < 0:
                raise ValidationError(_('Probation extension days cannot be negative.'))
    
    @api.constrains('date')
    def _check_date(self):
        for action in self:
            if action.date > fields.Date.today():
                raise ValidationError(_('Disciplinary action date cannot be in the future.'))
    
    def action_confirm(self):
        """Confirm the disciplinary action"""
        self.ensure_one()
        if self.state == 'draft':
            self.write({
                'state': 'confirmed',
                'confirmed_by': self.env.user,
                'confirmed_date': fields.Datetime.now()
            })
            
            # If it affects probation, extend the employee's probation
            if self.affects_probation and self.probation_extension_days > 0:
                employee = self.employee_id
                if employee.probation_end_date:
                    new_end_date = fields.Date.from_string(employee.probation_end_date) + \
                                 fields.timedelta(days=self.probation_extension_days)
                    employee.write({'probation_end_date': new_end_date})
    
    def action_activate(self):
        """Activate the disciplinary action"""
        self.ensure_one()
        if self.state in ['confirmed', 'resolved']:
            self.write({'state': 'active', 'active': True})
    
    def action_resolve(self):
        """Mark the disciplinary action as resolved"""
        self.ensure_one()
        if self.state == 'active':
            self.write({
                'state': 'resolved',
                'active': False,
                'resolution_date': fields.Date.today()
            })
    
    def action_cancel(self):
        """Cancel the disciplinary action"""
        self.ensure_one()
        self.write({'state': 'cancelled', 'active': False})
    
    def action_set_to_draft(self):
        """Set the disciplinary action back to draft"""
        self.ensure_one()
        if self.state in ['cancelled', 'confirmed']:
            self.write({
                'state': 'draft',
                'confirmed_by': False,
                'confirmed_date': False
            })
    
    def action_view_attachments(self):
        """View attachments for this disciplinary action"""
        self.ensure_one()
        action = self.env.ref('base.action_attachment').read()[0]
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.id,
        }
        action['domain'] = [('res_model', '=', self._name), ('res_id', '=', self.id)]
        action['view_mode'] = 'kanban,tree,form'
        return action
    
    def action_add_attachment(self):
        """Add attachment to disciplinary action"""
        self.ensure_one()
        action = self.env.ref('base.action_attachment').read()[0]
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.id,
        }
        action['view_mode'] = 'form'
        action['target'] = 'new'
        return action
    
    def _valid_field_parameter(self, field, name):
        """Override to handle deprecated tracking parameter"""
        if name == 'tracking':
            return True  # Accept but ignore the tracking parameter
        return super()._valid_field_parameter(field, name)
    
    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        
        # Send notification to HR managers when disciplinary actions are created
        for result in results:
            if result.employee_id:
                template = self.env.ref('surepay_hr_management.mail_template_disciplinary_action')
                hr_users = self.env['res.users'].search([
                    ('groups_id', 'in', [
                        self.env.ref('hr.group_hr_user').id,
                        self.env.ref('hr.group_hr_manager').id
                    ])
                ])
                
                for user in hr_users:
                    template.send_mail(
                        result.id,
                        email_values={
                            'email_to': user.email,
                            'recipient_ids': [(4, user.partner_id.id)]
                        }
                    )
        
        return results
    
    def write(self, vals):
        result = super().write(vals)
        
        # Send notification when state changes
        if 'state' in vals and vals['state'] in ['confirmed', 'active', 'resolved']:
            template = self.env.ref('surepay_hr_management.mail_template_disciplinary_action_status')
            hr_users = self.env['res.users'].search([
                ('groups_id', 'in', [
                    self.env.ref('hr.group_hr_user').id,
                    self.env.ref('hr.group_hr_manager').id
                ])
            ])
            
            for user in hr_users:
                template.send_mail(
                    self.id,
                    email_values={
                        'email_to': user.email,
                        'recipient_ids': [(4, user.partner_id.id)]
                    }
                )
        
        return result
    
    def unlink(self):
        """Override unlink to prevent deletion of non-draft records"""
        for action in self:
            if action.state != 'draft':
                raise ValidationError(_('You cannot delete a disciplinary action that is not in draft state.'))
        return super().unlink()
