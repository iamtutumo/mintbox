from odoo import models, fields, api, _


class HrSkill(models.Model):
    _name = 'hr.skill'
    _description = 'Skill'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Skill Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    skill_type_id = fields.Many2one('hr.skill.type', string='Skill Type', required=True)
    skill_level_id = fields.Many2one('hr.skill.level', string='Default Skill Level',
                                   help='Default skill level for this skill')
    active = fields.Boolean(string='Active', default=True)
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The skill name must be unique!')
    ]


class HrSkillType(models.Model):
    _name = 'hr.skill.type'
    _description = 'Skill Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Skill Type Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    skill_ids = fields.One2many('hr.skill', 'skill_type_id', string='Skills')
    skill_count = fields.Integer(string='Skill Count', compute='_compute_skill_count',
                                store=True)
    active = fields.Boolean(string='Active', default=True)
    
    @api.depends('skill_ids')
    def _compute_skill_count(self):
        for skill_type in self:
            skill_type.skill_count = len(skill_type.skill_ids)
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The skill type name must be unique!')
    ]


class HrSkillLevel(models.Model):
    _name = 'hr.skill.level'
    _description = 'Skill Level'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Level Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    level = fields.Integer(string='Level Order', help='Order of the level (lower number = lower level)')
    level_progress = fields.Integer(string='Level Progress', default=100, help='Progress percentage for this skill level')
    active = fields.Boolean(string='Active', default=True)
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The skill level name must be unique!')
    ]
    
    _order = 'level, name'

    @api.depends('has_skill_gap', 'skill_level_id', 'skill_id.skill_level_id')
    def _compute_gap_level(self):
        for employee_skill in self:
            # Only compute if the field is not already set (allowing manual override)
            if employee_skill.gap_level == 'none' and employee_skill.has_skill_gap:
                required_level = employee_skill.skill_id.skill_level_id
                current_level = employee_skill.skill_level_id
                
                if not required_level or not current_level:
                    employee_skill.gap_level = 'none'
                    continue
                
                gap_difference = required_level.level_rank - current_level.level_rank
                if gap_difference == 1:
                    employee_skill.gap_level = 'minor'
                else:
                    employee_skill.gap_level = 'major'
    
    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        return results
    
    def write(self, vals):
        result = super().write(vals)
        return result
    
    def _send_skill_fulfilled_notification(self):
        """Send notification when a required skill is fulfilled"""
        self.ensure_one()
        template = self.env.ref('surepay_hr_management.mail_template_skill_fulfilled')
        
        # Notify HR team
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

    

class HrSkillGapReport(models.Model):
    _name = 'hr.skill.gap.report'
    _description = 'HR Skill Gap Report'
    _auto = False
    
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    skill_id = fields.Many2one('hr.skill', string='Skill', readonly=True)
    current_level_id = fields.Many2one('hr.skill.level', string='Current Level', readonly=True)
    required_level_id = fields.Many2one('hr.skill.level', string='Required Level', readonly=True)
    gap_level = fields.Selection([
        ('none', 'No Gap'),
        ('minor', 'Minor Gap'),
        ('major', 'Major Gap')
    ], string='Gap Level', readonly=True)
    has_gap = fields.Boolean(string='Has Gap', readonly=True)
    
    @api.model
    def _select(self):
        return """
            SELECT 
                es.id as id,
                e.id as employee_id,
                e.department_id as department_id,
                s.id as skill_id,
                es.skill_level_id as current_level_id,
                NULL as required_level_id,
                CASE 
                    WHEN es.skill_level_id IS NULL THEN 'major'
                    ELSE 'none'
                END as gap_level,
                CASE 
                    WHEN es.skill_level_id IS NULL THEN true
                    ELSE false
                END as has_gap
        """
    
    @api.model
    def _from(self):
        return """
            FROM hr_employee e
            CROSS JOIN hr_skill s
            LEFT JOIN hr_employee_skill es ON e.id = es.employee_id AND s.id = es.skill_id
            WHERE e.active = true
        """
    
    @api.model
    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hr_skill_gap_report AS (
                %s
                %s
            )
        """ % (self._select(), self._from()))
