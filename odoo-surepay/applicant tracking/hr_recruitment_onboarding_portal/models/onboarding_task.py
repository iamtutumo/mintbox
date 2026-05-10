# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class OnboardingTask(models.Model):
    _name = 'onboarding.task'
    _description = 'Onboarding Task Template'
    _order = 'sequence, id'

    name = fields.Char(string='Task Name', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    required = fields.Boolean(string='Required', default=True)
    task_type = fields.Selection([
        ('document', 'Document Upload'),
        ('form', 'Form Completion'),
        ('training', 'Training/Orientation'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ], string='Task Type', default='other')
    responsible_id = fields.Many2one('res.users', string='Responsible Person')
    active = fields.Boolean(default=True)

class OnboardingTaskLine(models.Model):
    _name = 'onboarding.task.line'
    _description = 'Onboarding Task Instance'
    _order = 'sequence, id'

    onboarding_id = fields.Many2one('hr.applicant.onboarding', string='Onboarding', required=True, ondelete='cascade')
    task_id = fields.Many2one('onboarding.task', string='Task Template')
    name = fields.Char(string='Task Name', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    required = fields.Boolean(string='Required', default=True)
    task_type = fields.Selection([
        ('document', 'Document Upload'),
        ('form', 'Form Completion'),
        ('training', 'Training/Orientation'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ], string='Task Type', default='other')
    completed = fields.Boolean(string='Completed', default=False)
    completed_date = fields.Datetime(string='Completion Date')
    notes = fields.Text(string='Notes')
