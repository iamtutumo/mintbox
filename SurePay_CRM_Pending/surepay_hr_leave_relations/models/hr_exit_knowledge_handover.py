from odoo import models, fields, api, _


class HrExitKnowledgeHandover(models.Model):
    _name = 'hr.exit.knowledge.handover'
    _description = 'HR Exit Knowledge Handover'
    _order = 'sequence'
    
    clearance_id = fields.Many2one('hr.exit.clearance', string='Clearance',
                                  required=True, ondelete='cascade')
    
    knowledge_type = fields.Selection([
        ('process', 'Process'),
        ('project', 'Project'),
        ('client', 'Client'),
        ('system', 'System'),
        ('document', 'Document'),
        ('contact', 'Contact'),
        ('password', 'Password'),
        ('account', 'Account'),
        ('training', 'Training'),
        ('other', 'Other')
    ], string='Knowledge Type', required=True)
    
    title = fields.Char(string='Title', required=True)
    
    description = fields.Text(string='Description', required=True)
    
    handover_to = fields.Many2one('hr.employee', string='Handover To',
                                 domain="[('id', '!=', parent.employee_id)]")
    
    handover_date = fields.Date(string='Handover Date')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('not_required', 'Not Required')
    ], string='Status', default='pending', required=True)
    
    notes = fields.Text(string='Notes')
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    def action_completed(self):
        """Mark knowledge handover as completed"""
        self.write({
            'status': 'completed',
            'handover_date': fields.Date.today()
        })
    
    def action_not_required(self):
        """Mark knowledge handover as not required"""
        self.write({'status': 'not_required'})
    
    def action_reset_pending(self):
        """Reset status to pending"""
        self.write({'status': 'pending', 'handover_date': False, 'handover_to': False})
