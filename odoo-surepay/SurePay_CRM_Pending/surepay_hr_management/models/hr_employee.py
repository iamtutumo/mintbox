from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    # Skill Management Fields
    skill_ids = fields.One2many('hr.employee.skill', 'employee_id', string='Employee Skills')
    required_skill_ids = fields.Many2many('hr.skill', string='Required Skills',
                                         help='Skills required for this employee position')
    skill_gap_ids = fields.One2many('hr.skill.gap', 'employee_id', string='Skill Gaps')
    skill_gap_count = fields.Integer(string='Skill Gaps', compute='_compute_skill_gap_count',
                                    store=True, help='Number of active skill gaps for this employee')
    
    # Disciplinary Actions
    disciplinary_action_ids = fields.One2many('hr.disciplinary.action', 'employee_id', string='Disciplinary Actions')
    
    # Status and Analytics Fields
    probation_end_date = fields.Date(string='Probation End Date', 
                                   help='End date of probation period')
    is_on_probation = fields.Boolean(string='On Probation', compute='_compute_is_on_probation',
                                    store=True, help='Whether employee is currently on probation')
    disciplinary_action_count = fields.Integer(string='Disciplinary Actions',
                                             compute='_compute_disciplinary_action_count',
                                             store=True)
    active_disciplinary_count = fields.Integer(string='Active Disciplinary Actions',
                                             compute='_compute_active_disciplinary_count',
                                             store=True)
    
    # Contract Expiration Fields
    contract_expiration_days = fields.Integer(string='Days Until Contract Expiry',
                                            compute='_compute_contract_expiration_days',
                                            store=True)
    has_expiring_contract = fields.Boolean(string='Contract Expiring Soon',
                                         compute='_compute_has_expiring_contract',
                                         store=True)
    
    @api.depends('skill_gap_ids')
    def _compute_skill_gap_count(self):
        for employee in self:
            employee.skill_gap_count = len(employee.skill_gap_ids.filtered(lambda g: g.status != 'closed'))
    
    @api.depends('probation_end_date')
    def _compute_is_on_probation(self):
        today = fields.Date.today()
        for employee in self:
            employee.is_on_probation = employee.probation_end_date and employee.probation_end_date >= today
    
    @api.depends('disciplinary_action_ids')
    def _compute_disciplinary_action_count(self):
        for employee in self:
            employee.disciplinary_action_count = len(employee.disciplinary_action_ids)
    
    @api.depends('disciplinary_action_ids.active')
    def _compute_active_disciplinary_count(self):
        for employee in self:
            employee.active_disciplinary_count = len(employee.disciplinary_action_ids.filtered('active'))
    
    @api.depends('contract_ids.date_end')
    def _compute_contract_expiration_days(self):
        today = fields.Date.today()
        for employee in self:
            active_contracts = employee.contract_ids.filtered(lambda c: c.state == 'open' and c.date_end)
            if active_contracts:
                earliest_expiry = min(active_contracts.mapped('date_end'))
                employee.contract_expiration_days = (earliest_expiry - today).days
            else:
                employee.contract_expiration_days = False
    
    @api.depends('contract_expiration_days')
    def _compute_has_expiring_contract(self):
        for employee in self:
            employee.has_expiring_contract = employee.contract_expiration_days and employee.contract_expiration_days <= 30
    
    def action_view_skills(self):
        self.ensure_one()
        action = self.env.ref('surepay_hr_management.action_hr_employee_skill').read()[0]
        action['context'] = {'default_employee_id': self.id}
        action['domain'] = [('employee_id', '=', self.id)]
        return action
    
    def action_view_disciplinary_actions(self):
        self.ensure_one()
        action = self.env.ref('surepay_hr_management.action_hr_disciplinary_action').read()[0]
        action['context'] = {'default_employee_id': self.id}
        action['domain'] = [('employee_id', '=', self.id)]
        return action
    
    def action_view_skill_gaps(self):
        self.ensure_one()
        action = self.env.ref('surepay_hr_management.action_hr_skill_gap').read()[0]
        action['context'] = {
            'default_employee_id': self.id,
            'search_default_employee_id': self.id,
            'default_identified_by': self.env.user.id
        }
        action['domain'] = [('employee_id', '=', self.id)]
        return action
    
    @api.model
    def _check_contract_expirations(self):
        """Check for contracts expiring within 30 days and send notifications"""
        employees = self.search([('has_expiring_contract', '=', True)])
        template = self.env.ref('surepay_hr_management.mail_template_contract_expiration')
        
        for employee in employees:
            # Notify HR Officers and Managers
            hr_users = self.env['res.users'].search([
                ('groups_id', 'in', [
                    self.env.ref('hr.group_hr_user').id,
                    self.env.ref('hr.group_hr_manager').id
                ])
            ])
            
            for user in hr_users:
                template.send_mail(
                    employee.id,
                    email_values={
                        'email_to': user.email,
                        'recipient_ids': [(4, user.partner_id.id)]
                    }
                )
        
        return len(employees)
    
    def write(self, vals):
        result = super().write(vals)
        
        # Check if probation status changed
        if 'probation_end_date' in vals:
            self._check_probation_status()
        
        return result
    
    def _check_probation_status(self):
        """Check probation status and notify relevant parties"""
        for employee in self:
            if employee.is_on_probation:
                # Notify HR about probation status
                template = self.env.ref('surepay_hr_management.mail_template_probation_status')
                hr_users = self.env['res.users'].search([
                    ('groups_id', 'in', [
                        self.env.ref('hr.group_hr_user').id,
                        self.env.ref('hr.group_hr_manager').id
                    ])
                ])
                
                for user in hr_users:
                    template.send_mail(
                        employee.id,
                        email_values={
                            'email_to': user.email,
                            'recipient_ids': [(4, user.partner_id.id)]
                        }
                    )
