from odoo import models, fields, api, _


class HrEmployeeSkill(models.Model):
    # Check if the base model exists, if not create a minimal version
    _name = 'hr.employee.skill'
    _description = 'Employee Skill'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Basic fields that should exist in the base model
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    skill_id = fields.Many2one('hr.skill', string='Skill', required=True)
    skill_level_id = fields.Many2one('hr.skill.level', string='Level')
    skill_type_id = fields.Many2one('hr.skill.type', string='Type', related='skill_id.skill_type_id', store=True)
    
    # Additional fields for skill tracking
    date_acquired = fields.Date(string='Date Acquired', help='Date when the employee acquired this skill')
    description = fields.Text(string='Description', help='Additional details about the employee\'s skill')
    
    # Gap Analysis Fields (inherited from SurePay extension)
    is_required = fields.Boolean(string='Required Skill', default=False,
                                help='Mark if this skill is required for the employee')
    has_skill_gap = fields.Boolean(string='Skill Gap', default=False,
                                  help='Mark if there is a skill gap for this skill')
    gap_level = fields.Selection([
        ('none', 'No Gap'),
        ('minor', 'Minor Gap'),
        ('major', 'Major Gap')
    ], string='Gap Level', default='none', help='Level of the skill gap')
    
    # Level progress field
    level_progress = fields.Integer(string='Level Progress', compute='_compute_level_progress', store=True,
                                   help='Progress percentage for the current skill level')
    
    @api.depends('skill_level_id')
    def _compute_level_progress(self):
        for skill in self:
            if skill.skill_level_id:
                # Use a simple approach - if skill level is set, assume 100% progress
                # This can be enhanced later if there's a proper level ranking system
                skill.level_progress = 100
            else:
                skill.level_progress = 0
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure skill level is set for batch creation"""
        for vals in vals_list:
            if not vals.get('skill_level_id') and vals.get('skill_id'):
                skill = self.env['hr.skill'].browse(vals['skill_id'])
                if skill.skill_level_id:
                    vals['skill_level_id'] = skill.skill_level_id.id
        return super(HrEmployeeSkill, self).create(vals_list)
    
    def action_update_skill_level(self):
        """Action to update skill level - opens a wizard or dialog"""
        self.ensure_one()
        # For now, just return a simple action to open the form view
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
