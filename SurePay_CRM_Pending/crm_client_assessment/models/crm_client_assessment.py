from odoo import models, fields, api

class Service(models.Model):
    _name = 'crm.client.assessment.service'
    _description = 'Client Assessment Service'
    _order = 'sequence, name'
    
    name = fields.Char(string="Service Name", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class CustomerDistribution(models.Model):
    _name = 'crm.client.assessment.distribution'
    _description = 'Customer Distribution Channel'
    _order = 'sequence, name'
    
    name = fields.Char(string="Distribution Channel", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
