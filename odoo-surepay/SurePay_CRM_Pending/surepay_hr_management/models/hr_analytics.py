from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HrEmployeeAnalytics(models.Model):
    _name = 'hr.employee.analytics'
    _description = 'HR Employee Analytics'
    _auto = False
    
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    employee_count = fields.Integer(string='Employee Count', readonly=True)
    active_employee_count = fields.Integer(string='Active Employees', readonly=True)
    on_probation_count = fields.Integer(string='On Probation', readonly=True)
    contract_expiring_count = fields.Integer(string='Contracts Expiring Soon', readonly=True)
    disciplinary_action_count = fields.Integer(string='Disciplinary Action Count', readonly=True)
    skill_gap_count = fields.Integer(string='Skill Gap Count', readonly=True)
    
    # Date Fields
    date = fields.Date(string='Date', readonly=True)
    month = fields.Char(string='Month', readonly=True)
    year = fields.Integer(string='Year', readonly=True)
    
    @api.model
    def _select(self):
        return """
            SELECT 
                ROW_NUMBER() OVER () as id,
                d.id as department_id,
                COUNT(e.id) as employee_count,
                COUNT(CASE WHEN e.active = true THEN 1 END) as active_employee_count,
                COUNT(CASE WHEN e.is_on_probation = true THEN 1 END) as on_probation_count,
                COUNT(CASE WHEN e.has_expiring_contract = true THEN 1 END) as contract_expiring_count,
                COUNT(da.id) as disciplinary_action_count,
                0 as skill_gap_count,
                CURRENT_DATE as date,
                TO_CHAR(CURRENT_DATE, 'YYYY-MM') as month,
                EXTRACT(YEAR FROM CURRENT_DATE) as year
        """
    
    @api.model
    def _from(self):
        return """
            FROM hr_department d
            LEFT JOIN hr_employee e ON d.id = e.department_id
            LEFT JOIN hr_disciplinary_action da ON e.id = da.employee_id AND da.active = true
            LEFT JOIN hr_employee_skill es ON e.id = es.employee_id
        """
    
    @api.model
    def _group_by(self):
        return """
            GROUP BY d.id
        """
    
    @api.model
    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hr_employee_analytics AS (
                %s
                %s
                %s
            )
        """ % (self._select(), self._from(), self._group_by()))


class HrEmployeeStatusReport(models.Model):
    _name = 'hr.employee.status.report'
    _description = 'HR Employee Status Report'
    _auto = False
    
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', readonly=True)
    
    # Status Fields
    active = fields.Boolean(string='Active', readonly=True)
    is_on_probation = fields.Boolean(string='On Probation', readonly=True)
    has_expiring_contract = fields.Boolean(string='Contract Expiring Soon', readonly=True)
    has_disciplinary_actions = fields.Boolean(string='Has Disciplinary Actions', readonly=True)
    has_skill_gaps = fields.Boolean(string='Has Skill Gaps', readonly=True)
    
    # Count Fields
    disciplinary_action_count = fields.Integer(string='Disciplinary Actions', readonly=True)
    active_disciplinary_count = fields.Integer(string='Active Disciplinary Actions', readonly=True)
    skill_gap_count = fields.Integer(string='Skill Gaps', readonly=True)
    
    # Date Fields
    hire_date = fields.Date(string='Hire Date', readonly=True)
    probation_end_date = fields.Date(string='Probation End Date', readonly=True)
    contract_end_date = fields.Date(string='Contract End Date', readonly=True)
    
    @api.model
    def _select(self):
        return """
            SELECT 
                e.id as id,
                e.id as employee_id,
                e.department_id as department_id,
                e.job_id as job_id,
                e.parent_id as manager_id,
                e.active as active,
                e.is_on_probation as is_on_probation,
                e.has_expiring_contract as has_expiring_contract,
                CASE WHEN COUNT(da.id) > 0 THEN true ELSE false END as has_disciplinary_actions,
                false as has_skill_gaps,
                COUNT(da.id) as disciplinary_action_count,
                COUNT(CASE WHEN da.active = true THEN 1 END) as active_disciplinary_count,
                0 as skill_gap_count,
                e.create_date as hire_date,
                e.probation_end_date as probation_end_date,
                MAX(c.date_end) as contract_end_date
        """
    
    @api.model
    def _from(self):
        return """
            FROM hr_employee e
            LEFT JOIN hr_disciplinary_action da ON e.id = da.employee_id
            LEFT JOIN hr_employee_skill es ON e.id = es.employee_id
            LEFT JOIN hr_contract c ON e.id = c.employee_id AND c.state = 'open'
        """
    
    @api.model
    def _group_by(self):
        return """
            GROUP BY e.id, e.department_id, e.job_id, e.parent_id, e.active, 
                     e.is_on_probation, e.has_expiring_contract, e.create_date, 
                     e.probation_end_date
        """
    
    @api.model
    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hr_employee_status_report AS (
                %s
                %s
                %s
            )
        """ % (self._select(), self._from(), self._group_by()))


class HrDashboardWidget(models.Model):
    _name = 'hr.dashboard.widget'
    _description = 'HR Dashboard Widget'
    
    name = fields.Char(string='Widget Name', required=True)
    widget_type = fields.Selection([
        ('headcount', 'Headcount'),
        ('leave_balance', 'Leave Balance'),
        ('probation', 'Probation Status'),
        ('disciplinary', 'Disciplinary Actions'),
        ('skill_gaps', 'Skill Gaps'),
        ('contract_expiration', 'Contract Expiration'),
        ('turnover', 'Employee Turnover')
    ], string='Widget Type', required=True)
    
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    def get_widget_data(self):
        """Get data for the dashboard widget"""
        self.ensure_one()
        
        if self.widget_type == 'headcount':
            return self._get_headcount_data()
        elif self.widget_type == 'leave_balance':
            return self._get_leave_balance_data()
        elif self.widget_type == 'probation':
            return self._get_probation_data()
        elif self.widget_type == 'disciplinary':
            return self._get_disciplinary_data()
        elif self.widget_type == 'skill_gaps':
            return self._get_skill_gaps_data()
        elif self.widget_type == 'contract_expiration':
            return self._get_contract_expiration_data()
        elif self.widget_type == 'turnover':
            return self._get_turnover_data()
        
        return {}
    
    def _get_headcount_data(self):
        """Get headcount data"""
        total_employees = self.env['hr.employee'].search_count([('active', '=', True)])
        departments = self.env['hr.department'].search([('active', '=', True)])
        
        dept_data = []
        for dept in departments:
            count = self.env['hr.employee'].search_count([
                ('department_id', '=', dept.id),
                ('active', '=', True)
            ])
            dept_data.append({
                'department': dept.name,
                'count': count
            })
        
        return {
            'total': total_employees,
            'by_department': dept_data
        }
    
    def _get_leave_balance_data(self):
        """Get leave balance data"""
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        total_balance = 0
        employee_balances = []
        
        for employee in employees:
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('date_to', '>=', fields.Date.today())
            ])
            
            balance = sum(allocations.mapped('remaining_leaves'))
            total_balance += balance
            
            employee_balances.append({
                'employee': employee.name,
                'balance': balance
            })
        
        avg_balance = total_balance / len(employees) if employees else 0
        
        return {
            'total_balance': total_balance,
            'average_balance': avg_balance,
            'employee_balances': employee_balances
        }
    
    def _get_probation_data(self):
        """Get probation status data"""
        total_employees = self.env['hr.employee'].search_count([('active', '=', True)])
        on_probation = self.env['hr.employee'].search_count([
            ('active', '=', True),
            ('is_on_probation', '=', True)
        ])
        
        return {
            'total_employees': total_employees,
            'on_probation': on_probation,
            'percentage': (on_probation / total_employees * 100) if total_employees else 0
        }
    
    def _get_disciplinary_data(self):
        """Get disciplinary actions data"""
        total_actions = self.env['hr.disciplinary.action'].search_count([])
        active_actions = self.env['hr.disciplinary.action'].search_count([('active', '=', True)])
        
        return {
            'total_actions': total_actions,
            'active_actions': active_actions,
            'resolved_actions': total_actions - active_actions
        }
    
    def _get_skill_gaps_data(self):
        """Get skill gaps data"""
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        total_gaps = 0
        employees_with_gaps = 0
        
        for employee in employees:
            gaps = employee.skill_gap_count
            if gaps > 0:
                total_gaps += gaps
                employees_with_gaps += 1
        
        return {
            'total_gaps': total_gaps,
            'employees_with_gaps': employees_with_gaps,
            'total_employees': len(employees),
            'percentage_with_gaps': (employees_with_gaps / len(employees) * 100) if employees else 0
        }
    
    def _get_contract_expiration_data(self):
        """Get contract expiration data"""
        expiring_contracts = self.env['hr.contract'].search_count([
            ('is_expiring_soon', '=', True),
            ('state', '=', 'open')
        ])
        
        return {
            'expiring_contracts': expiring_contracts
        }
    
    def _get_turnover_data(self):
        """Get employee turnover data"""
        today = fields.Date.today()
        last_month = today - timedelta(days=30)
        
        active_employees = self.env['hr.employee'].search_count([('active', '=', True)])
        inactive_employees = self.env['hr.employee'].search_count([
            ('active', '=', False),
            ('write_date', '>=', last_month)
        ])
        
        return {
            'active_employees': active_employees,
            'recently_inactive': inactive_employees,
            'turnover_rate': (inactive_employees / (active_employees + inactive_employees) * 100) if (active_employees + inactive_employees) else 0
        }
