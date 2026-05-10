from odoo import models, fields, api, _


class HrSkillGap(models.Model):
    _name = 'hr.skill.gap'
    _description = 'HR Skill Gap'
    _order = 'date_identified desc, priority desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, 
                                 help='Employee who has the skill gap')
    identified_by = fields.Many2one('res.users', string='Identified By', required=True,
                                   default=lambda self: self.env.user,
                                   help='User who identified the skill gap')
    gap_title = fields.Char(string='Gap Title', required=True,
                           help='Short description of the missing skill (e.g., "Advanced Excel", "Customer Handling")')
    gap_description = fields.Text(string='Gap Description',
                                 help='Detailed description of the missing skill and why it\'s needed')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority', required=True, default='medium',
       help='Priority level of addressing this skill gap')
    date_identified = fields.Date(string='Date Identified', required=True,
                                 default=fields.Date.today(),
                                 help='Date when the skill gap was identified')
    status = fields.Selection([
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed')
    ], string='Status', required=True, default='open',
       help='Current status of the skill gap resolution')
    
    # Additional useful fields
    department_id = fields.Many2one(related='employee_id.department_id', string='Department',
                                   store=True, readonly=True, help='Department of the employee')
    manager_id = fields.Many2one(related='employee_id.parent_id', string='Manager',
                                store=True, readonly=True, help='Direct manager of the employee')
    job_id = fields.Many2one(related='employee_id.job_id', string='Job Position',
                            store=True, readonly=True, help='Job position of the employee')
    company_id = fields.Many2one(related='employee_id.company_id', string='Company',
                                store=True, readonly=True, help='Company of the employee')
    
    # Resolution fields
    resolution_notes = fields.Text(string='Resolution Notes',
                                  help='Notes about how the skill gap was addressed')
    date_resolved = fields.Date(string='Date Resolved',
                               help='Date when the skill gap was resolved')
    resolved_by = fields.Many2one('res.users', string='Resolved By',
                                 help='User who marked the skill gap as resolved')
    
    # Notification field
    notification_sent = fields.Boolean(string='Notification Sent', default=False,
                                     help='Whether notification has been sent for this skill gap')
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add logging for batch creation"""
        results = super().create(vals_list)
        # Send notification to manager if identified by someone else for each gap
        for result in results:
            if result.identified_by != result.employee_id.user_id and result.employee_id.parent_id:
                self._send_gap_notification(result, 'created')
        return results
    
    def write(self, vals):
        """Override write to handle status changes and notifications"""
        result = super().write(vals)
        
        # Handle status changes
        if 'status' in vals:
            for record in self:
                if vals['status'] == 'closed' and record.status != 'closed':
                    # Mark as resolved
                    record.write({
                        'date_resolved': fields.Date.today(),
                        'resolved_by': self.env.user
                    })
                elif vals['status'] == 'open' and record.status == 'closed':
                    # Reopen - clear resolution fields
                    record.write({
                        'date_resolved': False,
                        'resolved_by': False
                    })
                
                # Send notification for status changes
                self._send_gap_notification(record, 'status_changed')
        
        return result
    
    def _send_gap_notification(self, gap, action_type):
        """Send notification about skill gap actions"""
        try:
            # Get notification recipients
            recipients = []
            if gap.employee_id.parent_id and gap.employee_id.parent_id.user_id:
                recipients.append(gap.employee_id.parent_id.user_id.partner_id.id)
            if gap.employee_id.user_id and gap.employee_id.user_id != self.env.user:
                recipients.append(gap.employee_id.user_id.partner_id.id)
            
            if recipients:
                # Find HR managers
                hr_group = self.env.ref('hr.group_hr_manager')
                hr_users = hr_group.users.filtered(lambda u: u != self.env.user)
                for hr_user in hr_users:
                    if hr_user.partner_id.id not in recipients:
                        recipients.append(hr_user.partner_id.id)
                
                if recipients:
                    subject = _('Skill Gap %s: %s') % (
                        _('Created') if action_type == 'created' else _('Status Updated'),
                        gap.gap_title
                    )
                    message = _('Employee: %s\nGap: %s\nPriority: %s\nStatus: %s\nIdentified by: %s') % (
                        gap.employee_id.name,
                        gap.gap_title,
                        gap.priority,
                        gap.status,
                        gap.identified_by.name
                    )
                    
                    self.env['mail.thread'].message_notify(
                        partner_ids=recipients,
                        subject=subject,
                        body=message,
                        message_type='notification',
                        subtype_xmlid='mail.mt_comment',
                    )
        except Exception:
            # Don't fail if notification fails
            pass
    
    def action_set_in_progress(self):
        """Set skill gap status to In Progress"""
        self.write({'status': 'in_progress'})
        return True
    
    def action_set_closed(self):
        """Set skill gap status to Closed"""
        self.write({'status': 'closed'})
        return True
    
    def action_reopen(self):
        """Reopen a closed skill gap"""
        self.write({'status': 'open'})
        return True
    
    def action_send_notification(self):
        """Send notification about the skill gap"""
        for record in self:
            if not record.notification_sent:
                record._send_gap_notification(record, 'manual_notification')
                record.notification_sent = True
        return True
