# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrExitEquipmentReturn(models.Model):
    _name = 'hr.exit.equipment.return'
    _description = 'Exit Equipment Return'
    _order = 'clearance_id, sequence'
    
    clearance_id = fields.Many2one('hr.exit.clearance', string='Exit Clearance',
                                  required=True, ondelete='cascade')
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    item_description = fields.Char(string='Item Description', required=True)
    
    serial_number = fields.Char(string='Serial Number')
    
    date_returned = fields.Date(string='Date Returned')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('returned', 'Returned'),
        ('not_returned', 'Not Returned'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost')
    ], string='Status', default='pending', required=True)
    
    notes = fields.Text(string='Notes')
    
    returned_to = fields.Char(string='Returned To')
    
    condition_on_return = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Condition on Return')
    
    @api.model_create_multi
    def create(self, vals_list):
        equipments = super(HrExitEquipmentReturn, self).create(vals_list)
        # Update clearance status if all equipment is returned
        for equipment in equipments:
            if equipment.clearance_id:
                equipment.clearance_id._compute_all_equipment_returned()
        return equipments
    
    def write(self, vals):
        result = super(HrExitEquipmentReturn, self).write(vals)
        # Update clearance status if equipment status changed
        if 'status' in vals:
            for equipment in self:
                if equipment.clearance_id:
                    equipment.clearance_id._compute_all_equipment_returned()
        return result
