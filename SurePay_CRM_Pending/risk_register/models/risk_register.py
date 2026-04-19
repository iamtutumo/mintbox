from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class RiskRegister(models.Model):
    _name = 'risk.register'
    _description = 'Risk Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Risk Title', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Risk Level', required=True, default='medium', tracking=True)
    
    impact = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Impact', required=True, default='medium', tracking=True)
    
    likelihood = fields.Selection([
        ('rare', 'Rare'),
        ('possible', 'Possible'),
        ('likely', 'Likely'),
        ('almost_certain', 'Almost Certain'),
    ], string='Likelihood', required=True, default='possible', tracking=True)
    
    owner_id = fields.Many2one('res.users', string='Risk Owner', required=True, 
                              default=lambda self: self.env.user, tracking=True)
    
    identification_date = fields.Date(string='Date Identified', required=True, 
                                    default=fields.Date.today, tracking=True,
                                    help="Date when the risk was first identified")
    
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True,
                                 help="Person assigned to handle this risk")
    
    escalate_to_head = fields.Boolean(string='Escalate to Department Head', tracking=True,
                                    help="Check this box to escalate the risk to the department head")
    
    department_id = fields.Many2one('hr.department', string='Department', required=True, tracking=True)
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('mitigated', 'Mitigated'),
        ('closed', 'Closed'),
    ], string='Status', required=True, default='draft', tracking=True)
    
    mitigation_plan = fields.Text(string='Mitigation Plan', tracking=True)
    created_by = fields.Many2one('res.users', string='Created By', readonly=True, 
                                default=lambda self: self.env.user)
    
    # Computed fields for dashboard
    risk_score = fields.Integer(string='Risk Score', compute='_compute_risk_score', store=True, tracking=True)
    risk_score_color = fields.Char(string='Risk Score Color', compute='_compute_risk_score_color', store=True)
    risk_score_display = fields.Char(string='Risk Score Display', compute='_compute_risk_score_display', store=True)
    days_active = fields.Integer(string='Days Active', compute='_compute_days_active', store=True, tracking=True,
                               help="Number of days since the risk was identified")
    
    
    @api.depends('impact', 'likelihood')
    def _compute_risk_score(self):
        impact_values = {'low': 1, 'medium': 2, 'high': 3}
        likelihood_values = {'rare': 1, 'possible': 2, 'likely': 3, 'almost_certain': 4}
        
        for record in self:
            impact_score = impact_values.get(record.impact, 1)
            likelihood_score = likelihood_values.get(record.likelihood, 1)
            record.risk_score = impact_score * likelihood_score
    
    @api.depends('risk_score')
    def _compute_risk_score_color(self):
        for record in self:
            if not record.risk_score:
                record.risk_score_color = 'text-muted'  # Gray for no score
            elif record.risk_score <= 2:
                record.risk_score_color = 'text-success'  # Green for low risk
            elif record.risk_score <= 6:
                record.risk_score_color = 'text-warning'  # Yellow/Orange for medium risk
            else:
                record.risk_score_color = 'text-danger'   # Red for high risk
    
    @api.depends('risk_score', 'risk_score_color')
    def _compute_risk_score_display(self):
        for record in self:
            if not record.risk_score:
                record.risk_score_display = '⚪ No Score'  # White circle for no score
            elif record.risk_score <= 2:
                record.risk_score_display = f'🟢 {record.risk_score}'  # Green circle for low risk
            elif record.risk_score <= 6:
                record.risk_score_display = f'🟡 {record.risk_score}'  # Yellow circle for medium risk
            else:
                record.risk_score_display = f'🔴 {record.risk_score}'  # Red circle for high risk
    
    @api.depends('identification_date')
    def _compute_days_active(self):
        for record in self:
            if record.identification_date:
                # Calculate days between identification date and today
                delta = fields.Date.today() - record.identification_date
                record.days_active = delta.days
            else:
                record.days_active = 0
    
    @api.model
    def create(self, vals):
        # Handle batch creation
        if isinstance(vals, list):
            # Batch create multiple records
            records = []
            for val in vals:
                # Set department from user if not provided
                if not val.get('department_id') and self.env.user.employee_id:
                    val['department_id'] = self.env.user.employee_id.department_id.id
                records.append(val)
            
            # Create all records at once
            new_records = super().create(records)
            
            # Send notifications for new risks
            for record in new_records:
                if record.owner_id and record.owner_id != self.env.user:
                    self._send_status_notification(record, None, record.status)
            
            return new_records
        else:
            # Single record creation
            # Set department from user if not provided
            if not vals.get('department_id') and self.env.user.employee_id:
                vals['department_id'] = self.env.user.employee_id.department_id.id
            
            record = super().create(vals)
            
            # Send notification for new risk
            if record.owner_id and record.owner_id != self.env.user:
                self._send_status_notification(record, None, record.status)
            
            return record
    
    def action_save_and_return_to_dashboard(self):
        """Save record and return to dashboard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Risk Dashboard',
            'res_model': 'risk.register',
            'view_mode': 'form',
            'view_id': self.env.ref('risk_register.view_risk_dashboard').id,
            'target': 'current',
            'context': {'search_default_my_department': 1},
        }
    
    def action_save_and_create_new(self):
        """Save record and create new one"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Risk',
            'res_model': 'risk.register',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_department_id': self.department_id.id if self.department_id else False},
        }
    
    def write(self, vals):
        old_status = None
        if 'status' in vals:
            old_status = self.status
        
        # Store old values for audit trail
        old_values = {}
        for field_name in vals.keys():
            if hasattr(self, field_name):
                old_values[field_name] = {record.id: getattr(record, field_name) for record in self}
        
        result = super().write(vals)
        
        # Create audit log entries
        for field_name, new_value in vals.items():
            if field_name in old_values:
                for record_id, old_value in old_values[field_name].items():
                    # Handle Many2one fields
                    field_obj = self.env['risk.register']._fields[field_name]
                    if hasattr(field_obj, 'comodel_name') and field_obj.comodel_name:
                        # For Many2one fields, get the display name
                        old_val_display = old_value.name if old_value else ''
                        # For new_value, it might be an ID or a record object
                        if isinstance(new_value, int) and new_value:
                            new_record = self.env[field_obj.comodel_name].browse(new_value)
                            new_val_display = new_record.name if new_record.exists() else str(new_value)
                        elif hasattr(new_value, 'name'):
                            new_val_display = new_value.name
                        else:
                            new_val_display = str(new_value) if new_value else ''
                    else:
                        # For other field types, convert to string
                        old_val_display = str(old_value) if old_value is not None else ''
                        new_val_display = str(new_value) if new_value is not None else ''
                    
        
        # Send notification on status change
        if 'status' in vals and old_status != vals['status']:
            for record in self:
                if record.owner_id and record.owner_id != self.env.user:
                    self._send_status_notification(record, old_status, vals['status'])
        
        return result
    
    def _send_status_notification(self, record, old_status, new_status):
        """Send email notification on status change"""
        if not record.owner_id or not record.owner_id.email:
            return
        
        template = self.env.ref('risk_register.email_template_status_change')
        if template:
            template.with_context(old_status=old_status).send_mail(
                record.id,
                email_values={
                    'email_to': record.owner_id.email,
                    'email_from': self.env.user.email or self.env.company.email,
                }
            )
    
    def action_set_active(self):
        self.write({'status': 'active'})
    
    def action_set_mitigated(self):
        self.write({'status': 'mitigated'})
    
    def action_set_closed(self):
        self.write({'status': 'closed'})
    
    def action_export_pdf(self):
        """Export risk to PDF"""
        return self.env.ref('risk_register.action_report_risk_register').report_action(self)
    
    def action_export_excel(self):
        """Export risk to Excel"""
        risk_ids = self.ids
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/export/risk/excel?ids={",".join(map(str, risk_ids))}',
            'target': 'new',
        }
    
    def action_export_csv(self):
        """Export risk to CSV"""
        risk_ids = self.ids
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/export/risk/csv?ids={",".join(map(str, risk_ids))}',
            'target': 'new',
        }
    
    def _send_overdue_notification(self):
        """Send email notification for overdue risks"""
        if not self.owner_id or not self.owner_id.email:
            _logger.warning(f"Risk {self.name} has no owner with email address")
            return
        
        template = self.env.ref('risk_register.email_template_overdue_risk')
        if template:
            # Send to risk owner
            template.send_mail(
                self.id,
                email_values={
                    'email_to': self.owner_id.email,
                    'email_from': self.env.user.email or self.env.company.email,
                }
            )
            
            # Send to department head if available
            if self.department_id and self.department_id.manager_id and self.department_id.manager_id.email:
                template.send_mail(
                    self.id,
                    email_values={
                        'email_to': self.department_id.manager_id.email,
                        'email_from': self.env.user.email or self.env.company.email,
                    }
                )
            
            # Send to assigned person if different from owner
            if self.assigned_to and self.assigned_to.email and self.assigned_to != self.owner_id:
                template.send_mail(
                    self.id,
                    email_values={
                        'email_to': self.assigned_to.email,
                        'email_from': self.env.user.email or self.env.company.email,
                    }
                )
    
    @api.model
    def check_overdue_risks(self):
        """Check for overdue risks and send notifications"""
        overdue_days = 30  # Risks overdue after 30 days
        today = fields.Date.today()
        
        # Find active risks that are overdue
        overdue_risks = self.search([
            ('status', 'in', ['active', 'draft']),
            ('identification_date', '<=', today - fields.Date.timedelta(days=overdue_days)),
        ])
        
        _logger.info(f"Found {len(overdue_risks)} overdue risks")
        
        for risk in overdue_risks:
            try:
                risk._send_overdue_notification()
                _logger.info(f"Sent overdue notification for risk: {risk.name}")
            except Exception as e:
                _logger.error(f"Failed to send overdue notification for risk {risk.name}: {str(e)}")
        
        return True
    
    @api.model
    def _read_group_department_ids(self, departments, domain, order):
        """Read group for departments with access control"""
        if self.env.user.has_group('risk_register.group_risk_manager') or \
           self.env.user.has_group('risk_register.group_risk_admin'):
            return departments
        
        # Regular users can only see their department
        if self.env.user.employee_ids and self.env.user.employee_ids[0].department_id:
            user_department_id = self.env.user.employee_ids[0].department_id.id
            return departments.filtered(lambda d: d.id == user_department_id)
        
        return self.env['hr.department']
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        """Override search to apply department-based filtering"""
        # Apply department-based filtering for regular users
        if not (self.env.user.has_group('risk_register.group_risk_manager') or 
                self.env.user.has_group('risk_register.group_risk_admin')):
            
            if self.env.user.employee_ids and self.env.user.employee_ids[0].department_id:
                user_department_id = self.env.user.employee_ids[0].department_id.id
                # Add department filter to existing args
                department_domain = ['|', ('department_id', '=', False), ('department_id', '=', user_department_id)]
                if args:
                    args = ['&'] + args + department_domain
                else:
                    args = department_domain
        
        return super().search(args, offset=offset, limit=limit, order=order)
    
    # Standard Odoo access control is handled via ir.model.access.csv and record rules
    
    # Department-based access control is handled via record rules in security/risk_register_security.xml
    
    @api.model
    def get_dashboard_data(self):
        """Get dashboard data with department-based access control"""
        domain = []
        
        # Apply department-based filtering for regular users
        if not (self.env.user.has_group('risk_register.group_risk_manager') or 
                self.env.user.has_group('risk_register.group_risk_admin')):
            
            if self.env.user.employee_ids and self.env.user.employee_ids[0].department_id:
                user_department_id = self.env.user.employee_ids[0].department_id.id
                domain = ['|', ('department_id', '=', False), ('department_id', '=', user_department_id)]
            else:
                # User without department can see risks without department assignment
                domain = [('department_id', '=', False)]
        
        # Get all risks with applied domain
        risks = self.search(domain)
        
        # Calculate dashboard statistics
        stats = {
            'total_risks': len(risks),
            'risks_by_level': {
                'low': len(risks.filtered(lambda r: r.risk_level == 'low')),
                'medium': len(risks.filtered(lambda r: r.risk_level == 'medium')),
                'high': len(risks.filtered(lambda r: r.risk_level == 'high')),
                'critical': len(risks.filtered(lambda r: r.risk_level == 'critical')),
            },
            'risks_by_status': {
                'draft': len(risks.filtered(lambda r: r.status == 'draft')),
                'active': len(risks.filtered(lambda r: r.status == 'active')),
                'mitigated': len(risks.filtered(lambda r: r.status == 'mitigated')),
                'closed': len(risks.filtered(lambda r: r.status == 'closed')),
            },
            'risks_by_department': {},
            'overdue_risks': len(risks.filtered(lambda r: r.days_active >= 30)),
            'avg_risk_score': risks and sum(risks.mapped('risk_score')) / len(risks) or 0,
            'avg_days_active': risks and sum(risks.mapped('days_active')) / len(risks) or 0,
        }
        
        # Calculate risks by department
        for department in risks.mapped('department_id'):
            dept_risks = risks.filtered(lambda r: r.department_id == department)
            stats['risks_by_department'][department.name] = len(dept_risks)
        
        # Get risks created over time (last 12 months)
        from datetime import datetime
        end_date = fields.Date.today()
        start_date = end_date - timedelta(days=365)
        
        monthly_stats = {}
        current_date = start_date
        while current_date <= end_date:
            month_key = current_date.strftime('%Y-%m')
            month_start = current_date.replace(day=1)
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            monthly_risks = risks.filtered(
                lambda r: r.identification_date and month_start <= r.identification_date <= month_end
            )
            monthly_stats[month_key] = len(monthly_risks)
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        stats['risks_over_time'] = monthly_stats
        
        # Department and status breakdown
        department_status_breakdown = {}
        for department in risks.mapped('department_id'):
            dept_risks = risks.filtered(lambda r: r.department_id == department)
            department_status_breakdown[department.name] = {
                'draft': len(dept_risks.filtered(lambda r: r.status == 'draft')),
                'active': len(dept_risks.filtered(lambda r: r.status == 'active')),
                'mitigated': len(dept_risks.filtered(lambda r: r.status == 'mitigated')),
                'closed': len(dept_risks.filtered(lambda r: r.status == 'closed')),
            }
        stats['department_status_breakdown'] = department_status_breakdown
        
        # Impact vs Likelihood matrix
        impact_likelihood_matrix = {}
        impacts = ['Low', 'Medium', 'High']
        likelihoods = ['Low', 'Medium', 'High']
        
        for impact in impacts:
            for likelihood in likelihoods:
                key = f"{impact}_{likelihood}"
                count = len(risks.filtered(
                    lambda r: r.impact == impact.lower() and r.likelihood == likelihood.lower()
                ))
                impact_likelihood_matrix[key] = count
        
        stats['impact_likelihood_matrix'] = impact_likelihood_matrix
        
        # Risk distribution by category (based on risk score ranges)
        risk_distribution = {
            'Very Low (1-3)': len(risks.filtered(lambda r: r.risk_score <= 3)),
            'Low (4-6)': len(risks.filtered(lambda r: 4 <= r.risk_score <= 6)),
            'Medium (7-9)': len(risks.filtered(lambda r: 7 <= r.risk_score <= 9)),
            'High (10-12)': len(risks.filtered(lambda r: 10 <= r.risk_score <= 12)),
            'Critical (13-15)': len(risks.filtered(lambda r: r.risk_score >= 13)),
        }
        stats['risk_distribution'] = risk_distribution
        
        # Overdue analysis
        overdue_risks = risks.filtered(lambda r: r.days_active >= 30)
        stats['overdue_analysis'] = {
            'avg_days_overdue': overdue_risks and sum(overdue_risks.mapped('days_active')) / len(overdue_risks) or 0,
            'max_days_overdue': overdue_risks and max(overdue_risks.mapped('days_active')) or 0,
        }
        
        # Top high-risk items (risks with score >= 10)
        high_risks = risks.filtered(lambda r: r.risk_score >= 10).sorted('risk_score', reverse=True)[:5]
        stats['top_high_risks'] = [{
            'name': risk.name,
            'department': risk.department_id.name if risk.department_id else 'No Department',
            'risk_score': risk.risk_score,
            'days_active': risk.days_active,
        } for risk in high_risks]
        
        # Recent activities (from audit logs)
        AuditLog = self.env['risk.register.audit.log']
        recent_logs = AuditLog.search([
            ('risk_id', 'in', risks.ids),
            ('create_date', '>=', fields.Datetime.now() - timedelta(days=7))
        ], order='create_date desc', limit=10)
        
        stats['recent_activities'] = [{
            'description': log.field_name.replace('_', ' ').title() + ' Changed',
            'user': log.user_id.name,
            'risk_name': log.risk_id.name,
            'date': log.create_date.strftime('%Y-%m-%d %H:%M'),
            'details': f"From '{log.old_value}' to '{log.new_value}'",
        } for log in recent_logs]
        
        # Add mitigated risks count
        stats['mitigated_risks'] = len(risks.filtered(lambda r: r.status == 'mitigated'))
        
        return stats
