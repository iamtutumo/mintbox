from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    # Contract Expiration Fields
    expiration_date = fields.Date(string='Expiration Date', 
                                 help='Date when contract/certification expires')
    expiration_notification_sent = fields.Boolean(string='Expiration Notification Sent',
                                                 default=False,
                                                 help='Whether expiration notification has been sent')
    days_until_expiration = fields.Integer(string='Days Until Expiration',
                                         compute='_compute_days_until_expiration',
                                         store=True)
    is_expiring_soon = fields.Boolean(string='Expiring Soon',
                                    compute='_compute_is_expiring_soon',
                                    store=True)
    
    # Certification Fields
    certification_type = fields.Selection([
        ('contract', 'Employment Contract'),
        ('professional', 'Professional Certification'),
        ('safety', 'Safety Certification'),
        ('technical', 'Technical Certification'),
        ('other', 'Other')
    ], string='Certification Type', default='contract')
    
    certification_number = fields.Char(string='Certification Number')
    issuing_authority = fields.Char(string='Issuing Authority')
    
    @api.depends('expiration_date')
    def _compute_days_until_expiration(self):
        today = fields.Date.today()
        for contract in self:
            if contract.expiration_date:
                contract.days_until_expiration = (contract.expiration_date - today).days
            else:
                contract.days_until_expiration = False
    
    @api.depends('days_until_expiration')
    def _compute_is_expiring_soon(self):
        for contract in self:
            contract.is_expiring_soon = (contract.days_until_expiration is not False and 
                                       contract.days_until_expiration <= 30 and 
                                       contract.days_until_expiration >= 0)
    
    @api.model
    def check_contract_expirations(self):
        """Daily cron job to check for expiring contracts and send notifications"""
        today = fields.Date.today()
        expiring_contracts = self.search([
            ('expiration_date', '<=', today + fields.timedelta(days=30)),
            ('expiration_date', '>=', today),
            ('expiration_notification_sent', '=', False),
            ('state', '=', 'open')
        ])
        
        template = self.env.ref('surepay_hr_management.mail_template_contract_expiration')
        
        for contract in expiring_contracts:
            # Notify HR Officers and Managers
            hr_users = self.env['res.users'].search([
                ('groups_id', 'in', [
                    self.env.ref('hr.group_hr_user').id,
                    self.env.ref('hr.group_hr_manager').id
                ])
            ])
            
            for user in hr_users:
                template.send_mail(
                    contract.id,
                    email_values={
                        'email_to': user.email,
                        'recipient_ids': [(4, user.partner_id.id)]
                    }
                )
            
            # Mark notification as sent
            contract.expiration_notification_sent = True
        
        return len(expiring_contracts)
    
    @api.constrains('expiration_date')
    def _check_expiration_date(self):
        for contract in self:
            if contract.expiration_date and contract.expiration_date < fields.Date.today():
                raise ValidationError(_('Expiration date cannot be in the past.'))
    
    def action_send_expiration_notification(self):
        """Manually send expiration notification for this contract"""
        self.ensure_one()
        if not self.expiration_date:
            raise ValidationError(_('Cannot send notification: No expiration date set.'))
        
        template = self.env.ref('surepay_hr_management.mail_template_contract_expiration')
        
        # Notify HR Officers and Managers
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
        
        self.expiration_notification_sent = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Notification Sent'),
                'message': _('Expiration notification sent to HR team.'),
                'type': 'success',
            }
        }
    
    def write(self, vals):
        result = super().write(vals)
        
        # Reset notification flag if expiration date is changed
        if 'expiration_date' in vals:
            self.write({'expiration_notification_sent': False})
        
        return result
