from odoo import models, fields, api, _


class HrExitAssetReturn(models.Model):
    _name = 'hr.exit.asset.return'
    _description = 'HR Exit Asset Return'
    _order = 'sequence'
    
    clearance_id = fields.Many2one('hr.exit.clearance', string='Clearance',
                                  required=True, ondelete='cascade')
    
    asset_type = fields.Selection([
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('phone', 'Phone'),
        ('tablet', 'Tablet'),
        ('access_card', 'Access Card'),
        ('keys', 'Keys'),
        ('uniform', 'Uniform'),
        ('equipment', 'Equipment'),
        ('documents', 'Documents'),
        ('other', 'Other')
    ], string='Asset Type', required=True)
    
    asset_name = fields.Char(string='Asset Name', required=True)
    
    asset_description = fields.Text(string='Asset Description')
    
    serial_number = fields.Char(string='Serial Number')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('returned', 'Returned'),
        ('not_returned', 'Not Returned'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost')
    ], string='Status', default='pending', required=True)
    
    return_date = fields.Date(string='Return Date')
    
    returned_to = fields.Many2one('res.users', string='Returned To')
    
    notes = fields.Text(string='Notes')
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    def action_returned(self):
        """Mark asset as returned"""
        self.write({
            'status': 'returned',
            'return_date': fields.Date.today(),
            'returned_to': self.env.user.id
        })
    
    def action_not_returned(self):
        """Mark asset as not returned"""
        self.write({'status': 'not_returned'})
    
    def action_damaged(self):
        """Mark asset as damaged"""
        self.write({'status': 'damaged'})
    
    def action_lost(self):
        """Mark asset as lost"""
        self.write({'status': 'lost'})
    
    def action_reset_pending(self):
        """Reset status to pending"""
        self.write({'status': 'pending', 'return_date': False, 'returned_to': False})
