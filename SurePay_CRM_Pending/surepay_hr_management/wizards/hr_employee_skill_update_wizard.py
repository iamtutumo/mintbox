from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployeeSkillUpdateWizard(models.TransientModel):
    _name = 'hr.employee.skill.update.wizard'
    _description = 'HR Employee Skill Update Wizard'
    
    employee_skill_id = fields.Many2one('hr.employee.skill', string='Employee Skill',
                                       required=True)
    skill_level_id = fields.Many2one('hr.skill.level', string='Skill Level', required=True)
    
    date_acquired = fields.Date(string='Date Acquired', default=fields.Date.today())
    description = fields.Text(string='Description/Notes')
    
    def action_update_skill(self):
        """Update the employee skill"""
        self.ensure_one()
        
        if not self.employee_skill_id:
            raise ValidationError(_('Please select an employee skill to update.'))
        
        # Update the skill
        self.employee_skill_id.write({
            'skill_level_id': self.skill_level_id.id,
            'date_acquired': self.date_acquired,
            'description': self.description,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
