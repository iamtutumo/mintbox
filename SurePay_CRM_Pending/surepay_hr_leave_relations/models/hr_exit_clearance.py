from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
import base64
import os
import secrets


class HrExitClearance(models.Model):
    _name = 'hr.exit.clearance'
    _description = 'HR Exit Clearance'
    _order = 'request_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                   store=True, readonly=True)
    
    manager_id = fields.Many2one('hr.employee', string='Department Manager', related='employee_id.parent_id',
                                 store=True, readonly=True)
    
    hr_manager_id = fields.Many2one('hr.employee', string='HR Manager', compute='_compute_hr_manager',
                                   store=True, readonly=True)
    
    it_manager_id = fields.Many2one('hr.employee', string='IT Manager', compute='_compute_it_manager',
                                   store=True, readonly=True)
    
    finance_manager_id = fields.Many2one('hr.employee', string='Finance Manager', compute='_compute_finance_manager',
                                       store=True, readonly=True)
    
    request_date = fields.Date(string='Request Date', required=True,
                              default=fields.Date.today(),
                              readonly=True)
    
    last_working_day = fields.Date(string='Last Working Day', required=True)
    
    exit_reason = fields.Text(string='Exit Reason', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('manager_approval', 'Manager Approval'),
        ('hr_review', 'HR Review'),
        ('department_clearance', 'Department Clearance'),
        ('final_clearance', 'Final Clearance'),
        ('cleared', 'Cleared'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True)
    
    clearance_line_ids = fields.One2many('hr.exit.clearance.line', 'clearance_id',
                                        string='Clearance Lines')
    
    asset_return_ids = fields.One2many('hr.exit.asset.return', 'clearance_id',
                                      string='Asset Returns')
    
    knowledge_handover_ids = fields.One2many('hr.exit.knowledge.handover', 'clearance_id',
                                           string='Knowledge Handover')
    
    final_interview_date = fields.Date(string='Interview Date',
                                     readonly=True)
    
    final_interview_notes = fields.Text(string='Final Interview Notes',
                                      readonly=True)
    
    # Employee Information from Exit Form
    supervisor_name = fields.Char(string='Supervisor Name',
                                readonly=True)
    
    supervisor_title = fields.Char(string='Supervisor Title',
                                  readonly=True)
    
    length_of_service = fields.Char(string='Length of Service', compute='_compute_length_of_service',
                                   store=True, readonly=True)
    
    # Reason for Leaving Categories
    reason_for_leaving_category = fields.Selection([
        ('resignation', 'Resignation'),
        ('another_position', 'Took another position'),
        ('home_family', 'Home/family needs'),
        ('health', 'Health'),
        ('relocation', 'Relocation'),
        ('travel_requirements', 'Travel requirements'),
        ('lack_of_training', 'Lack of training'),
        ('lack_of_opportunities', 'Lack of opportunities'),
        ('culture', 'Culture'),
        ('return_to_study', 'To return to study'),
        ('dissatisfaction_work', 'Dissatisfaction with type of work'),
        ('dissatisfaction_salary', 'Dissatisfaction with salary/benefits'),
        ('dissatisfaction_conditions', 'Dissatisfaction with working conditions'),
        ('laid_off', 'Laid Off'),
        ('poor_performance', 'Poor performance'),
        ('inappropriate_conduct', 'Inappropriate Conduct'),
        ('violation_policy', 'Violation of Company Policy'),
        ('retirement', 'Retirement'),
        ('other', 'Other')
    ], string='Reason for Leaving Category', readonly=True)
    
    reason_for_leaving_other = fields.Char(string='Other Reason',
                                         readonly=True)
    
    # Employee Feedback Sections
    decision_factors = fields.Text(string='Factors contributing to decision to leave',
                                  readonly=True)
    
    most_satisfying = fields.Text(string='Most satisfying aspects of role',
                                 readonly=True)
    
    least_satisfying = fields.Text(string='Least satisfying aspects of role',
                                  readonly=True)
    
    job_duties_as_expected = fields.Text(string='Did job duties turn out as expected?',
                                        readonly=True)
    
    improvement_suggestions = fields.Text(string='Suggestions for improving the company',
                                        readonly=True)
    
    # Acknowledgements
    employee_signature = fields.Binary(string='Employee Signature',
                                     readonly=True, attachment=True)
    
    employee_signature_date = fields.Date(string='Employee Signature Date',
                                        readonly=True)
    
    hr_supervisor_signature = fields.Binary(string='HR/Supervisor Signature',
                                          readonly=True, attachment=True)
    
    hr_supervisor_signature_date = fields.Date(string='HR/Supervisor Signature Date',
                                             readonly=True)
    
    # Equipment and Assets Return
    equipment_return_ids = fields.One2many('hr.exit.equipment.return', 'clearance_id',
                                         string='Equipment Returns')
    
    all_equipment_returned = fields.Boolean(string='All Equipment Returned', 
                                          compute='_compute_all_equipment_returned',
                                          store=True)
    
    all_cleared = fields.Boolean(string='All Cleared', compute='_compute_all_cleared',
                                store=True)
    
    clearance_form_generated = fields.Boolean(string='Clearance Form Generated',
                                           default=False)
    
    exit_interview_form_generated = fields.Boolean(string='Exit Interview Form Generated',
                                                 default=False)
    
    security_token = fields.Char(string='Security Token', copy=False, readonly=True)
    
    clearance_form_attachment_id = fields.Many2one('ir.attachment',
                                                  string='Clearance Form Attachment')
    
    clearance_form_filename = fields.Char(string='Clearance Form Filename')
    
    exit_interview_form_attachment_id = fields.Many2one('ir.attachment',
                                                        string='Exit Interview Form Attachment')
    
    exit_interview_form_filename = fields.Char(string='Exit Interview Form Filename')
    
    @api.depends('clearance_line_ids.status')
    def _compute_all_cleared(self):
        for clearance in self:
            if clearance.clearance_line_ids:
                clearance.all_cleared = all(line.status == 'cleared' 
                                          for line in clearance.clearance_line_ids)
            else:
                clearance.all_cleared = False
    
    @api.depends('employee_id', 'last_working_day')
    def _compute_length_of_service(self):
        for clearance in self:
            if clearance.employee_id and clearance.employee_id.create_date and clearance.last_working_day:
                start_date = fields.Date.from_string(clearance.employee_id.create_date)
                end_date = clearance.last_working_day
                
                # Calculate years, months, days
                years = end_date.year - start_date.year
                months = end_date.month - start_date.month
                days = end_date.day - start_date.day
                
                if days < 0:
                    months -= 1
                    days += 30  # Approximate
                
                if months < 0:
                    years -= 1
                    months += 12
                
                if years > 0:
                    clearance.length_of_service = f"{years} years, {months} months"
                elif months > 0:
                    clearance.length_of_service = f"{months} months, {days} days"
                else:
                    clearance.length_of_service = f"{days} days"
            else:
                clearance.length_of_service = ''
    
    @api.depends('equipment_return_ids.status')
    def _compute_all_equipment_returned(self):
        for clearance in self:
            if clearance.equipment_return_ids:
                clearance.all_equipment_returned = all(
                    equipment.status == 'returned' 
                    for equipment in clearance.equipment_return_ids
                )
            else:
                clearance.all_equipment_returned = False
    
    @api.depends('department_id')
    def _compute_hr_manager(self):
        for clearance in self:
            if clearance.department_id:
                # Find HR manager from HR department
                hr_department = self.env['hr.department'].search([('name', '=', 'Human Resources')], limit=1)
                if hr_department:
                    hr_manager = self.env['hr.employee'].search([
                        ('department_id', '=', hr_department.id),
                        ('parent_id', '=', False)  # Top-level HR employee
                    ], limit=1)
                    clearance.hr_manager_id = hr_manager.id if hr_manager else False
                else:
                    clearance.hr_manager_id = False
            else:
                clearance.hr_manager_id = False
    
    @api.depends('department_id')
    def _compute_it_manager(self):
        for clearance in self:
            if clearance.department_id:
                # Find IT manager from IT department
                it_department = self.env['hr.department'].search([('name', '=', 'IT')], limit=1)
                if it_department:
                    it_manager = self.env['hr.employee'].search([
                        ('department_id', '=', it_department.id),
                        ('parent_id', '=', False)  # Top-level IT employee
                    ], limit=1)
                    clearance.it_manager_id = it_manager.id if it_manager else False
                else:
                    clearance.it_manager_id = False
            else:
                clearance.it_manager_id = False
    
    @api.depends('department_id')
    def _compute_finance_manager(self):
        for clearance in self:
            if clearance.department_id:
                # Find Finance manager from Finance department
                finance_department = self.env['hr.department'].search([('name', '=', 'Finance')], limit=1)
                if finance_department:
                    finance_manager = self.env['hr.employee'].search([
                        ('department_id', '=', finance_department.id),
                        ('parent_id', '=', False)  # Top-level Finance employee
                    ], limit=1)
                    clearance.finance_manager_id = finance_manager.id if finance_manager else False
                else:
                    clearance.finance_manager_id = False
            else:
                clearance.finance_manager_id = False
    
    def action_submit(self):
        self.write({'state': 'submitted'})
        self._create_clearance_lines()
        self._create_asset_returns()
        self._create_knowledge_handover()
        self._notify_manager()
    
    def action_manager_approve(self):
        self.write({'state': 'manager_approval'})
        self._notify_hr()
    
    def action_hr_review(self):
        self.write({'state': 'hr_review'})
        self._notify_departments()
    
    def action_start_clearance(self):
        self.write({'state': 'department_clearance'})
    
    def action_final_clearance(self):
        self.write({'state': 'final_clearance'})
        self._schedule_final_interview()
    
    def action_generate_clearance_form(self):
        self.write({'clearance_form_generated': True})
        self._generate_clearance_form()
        self._send_clearance_form_email()
    
    def action_approve(self):
        self.write({'state': 'cleared'})
        self._notify_employee_clearance()
    
    def action_reject(self):
        self.write({'state': 'rejected'})
        self._notify_employee_rejection()
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_reset_draft(self):
        self.write({'state': 'draft'})
    
    def _create_clearance_lines(self):
        """Create clearance lines for each department"""
        departments = [
            ('IT', 'IT Department'),
            ('Sales', 'Sales Department'),
            ('Marketing', 'Marketing Department'),
            ('Finance', 'Finance Department'),
            ('Management', 'Management Department'),
            ('Customer Service', 'Customer Service Department')
        ]
        
        for dept_code, dept_name in departments:
            self.env['hr.exit.clearance.line'].create({
                'clearance_id': self.id,
                'department': dept_code,
                'department_name': dept_name,
                'status': 'pending'
            })
    
    def _create_asset_returns(self):
        """Create asset return records for common company assets"""
        common_assets = [
            ('laptop', 'Company Laptop'),
            ('phone', 'Company Phone'),
            ('access_card', 'Employee ID Card'),
            ('keys', 'Office Keys'),
            ('access_card', 'Access Card'),
            ('uniform', 'Company Uniform'),
            ('other', 'Other Assets')
        ]
        
        for asset_type, asset_name in common_assets:
            self.env['hr.exit.asset.return'].create({
                'clearance_id': self.id,
                'asset_type': asset_type,
                'asset_name': asset_name,
                'status': 'pending'
            })
    
    def _create_knowledge_handover(self):
        """Create knowledge handover records"""
        handover_items = [
            ('project', 'Active Projects'),
            ('client', 'Client Relationships'),
            ('process', 'Department Processes'),
            ('document', 'Important Documents'),
            ('contact', 'Key Contacts'),
            ('password', 'System Passwords'),
            ('other', 'Other Knowledge')
        ]
        
        for item_type, item_name in handover_items:
            self.env['hr.exit.knowledge.handover'].create({
                'clearance_id': self.id,
                'knowledge_type': item_type,
                'title': item_name,
                'description': f'Please handover {item_name.lower()} information and processes',
                'status': 'pending'
            })
    
    def _notify_manager(self):
        """Notify department manager about exit request"""
        if self.manager_id and self.manager_id.work_email:
            template = self.env.ref('surepay_hr_leave_relations.email_template_exit_clearance_manager')
            if template:
                template.send_mail(self.id, force_send=True)
    
    def _notify_hr(self):
        """Notify HR about manager approval"""
        if self.hr_manager_id and self.hr_manager_id.work_email:
            template = self.env.ref('surepay_hr_leave_relations.email_template_exit_clearance_hr')
            if template:
                template.send_mail(self.id, force_send=True)
    
    def _notify_departments(self):
        """Send notification to relevant departments"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_exit_clearance_notification')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _schedule_final_interview(self):
        """Schedule final interview with HR"""
        self.write({'final_interview_date': fields.Date.today() + timedelta(days=3)})
        if self.hr_manager_id and self.hr_manager_id.work_email:
            template = self.env.ref('surepay_hr_leave_relations.email_template_exit_interview')
            if template:
                template.send_mail(self.id, force_send=True)
    
    def _notify_employee_clearance(self):
        """Notify employee about clearance completion"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_exit_clearance_complete')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _notify_employee_rejection(self):
        """Notify employee about clearance rejection"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_exit_clearance_rejected')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _generate_clearance_form(self):
        """Generate clearance form PDF"""
        # This would typically integrate with a report generation system
        # For now, we'll just mark it as generated
        self.clearance_form_generated = True
    
    def _send_clearance_form_email(self):
        """Send clearance form email to HR Manager and employee"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_clearance_form_completed')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _generate_exit_interview_form(self):
        """Generate comprehensive exit interview form"""
        # This would typically integrate with a report generation system
        # For now, we'll just mark it as generated
        self.exit_interview_form_generated = True
    
    def _send_exit_form_email(self):
        """Send exit interview form email to HR Manager and employee"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_exit_interview_form_completed')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _notify_employee_interview_complete(self):
        """Notify employee about interview completion"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_exit_interview_complete')
        if template:
            template.send_mail(self.id, force_send=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        clearances = super(HrExitClearance, self).create(vals_list)
        # Auto-notify manager if available
        for clearance in clearances:
            if clearance.manager_id:
                clearance._notify_manager()
        return clearances
    
    @api.constrains('last_working_day')
    def _check_last_working_day(self):
        for clearance in self:
            if clearance.last_working_day and clearance.last_working_day < clearance.request_date:
                raise ValidationError(_('Last working day must be after request date.'))

    def _get_clearance_form_content(self):
        """Generate clearance form content"""
        content = f"""
        EXIT CLEARANCE FORM
        ===================
        
        Employee Details:
        Name: {self.employee_id.name}
        Employee ID: {self.employee_id.work_email or 'N/A'}
        Department: {self.employee_id.department_id.name or 'N/A'}
        Position: {self.employee_id.job_id.name or 'N/A'}
        
        Clearance Details:
        Request Date: {self.request_date}
        Last Working Day: {self.last_working_day}
        Exit Reason: {self.exit_reason}
        
        Department Clearances:
        """
        
        for line in self.clearance_line_ids:
            content += f"""
        {line.department_name}:
        Status: {line.status}
        Cleared By: {line.cleared_by.name if line.cleared_by else 'N/A'}
        Date: {line.clearance_date or 'N/A'}
        Notes: {line.notes or 'N/A'}
        """
        
        return content
    
    def _get_exit_interview_form_content(self):
        """Generate comprehensive exit interview form content"""
        content = f"""
        EMPLOYEE EXIT INTERVIEW FORM
        =============================
        
        Interview Date: {self.final_interview_date or 'N/A'}
        
        Employee Information:
        Name: {self.employee_id.name}
        Title/Department: {self.employee_id.job_id.name or 'N/A'} / {self.employee_id.department_id.name or 'N/A'}
        Supervisor Name: {self.supervisor_name or 'N/A'}
        Supervisor Title: {self.supervisor_title or 'N/A'}
        Last Date of Work: {self.last_working_day or 'N/A'}
        Length of Service: {self.length_of_service or 'N/A'}
        
        Reason for Leaving:
        Category: {dict(self._fields['reason_for_leaving_category'].selection).get(self.reason_for_leaving_category, 'N/A')}
        Other: {self.reason_for_leaving_other or 'N/A'}
        
        Employee Feedback:
        
        What factors contributed to your decision to leave the company?
        {self.decision_factors or 'N/A'}
        
        What did you find most satisfying about your role?
        {self.most_satisfying or 'N/A'}
        
        What did you find least satisfying about your role?
        {self.least_satisfying or 'N/A'}
        
        Did your job duties turn out as expected?
        {self.job_duties_as_expected or 'N/A'}
        
        What suggestions do you have for improving the company?
        {self.improvement_suggestions or 'N/A'}
        
        Employee Acknowledgement:
        I hereby acknowledge that I have provided accurate information in this Employee Exit Form. 
        I also acknowledge that I have returned all company property and equipment (if any) assigned to me during my employment.
        
        Employee Signature Date: {self.employee_signature_date or 'N/A'}
        
        HR / Supervisor Acknowledgement:
        I hereby acknowledge that the information provided in this Employee Exit Form has been reviewed. 
        I also acknowledge receipt of all company property and equipment (if any) from the employee.
        
        HR / Supervisor Signature Date: {self.hr_supervisor_signature_date or 'N/A'}
        
        Note: This Employee Exit Form is confidential and should be kept in the employee's personnel file.
        
        Equipment and Assets Return:
        """
        
        for equipment in self.equipment_return_ids:
            content += f"""
        Item Description: {equipment.item_description}
        Serial Number: {equipment.serial_number or 'N/A'}
        Date Returned: {equipment.date_returned or 'N/A'}
        Status: {equipment.status}
        Condition: {dict(equipment._fields['condition_on_return'].selection).get(equipment.condition_on_return, 'N/A') if equipment.condition_on_return else 'N/A'}
        Notes: {equipment.notes or 'N/A'}
        """
        
        return content
    
    def _send_clearance_form_email(self):
        """Send clearance form email to HR Manager and employee"""
        template = self.env.ref('surepay_hr_leave_relations.email_template_clearance_form_completed')
        if template:
            template.send_mail(self.id, force_send=True)
    
    def _generate_security_token(self):
        """Generate a security token for form submissions"""
        import secrets
        import base64
        token = secrets.token_urlsafe(32)
        return token
    
    def action_send_exit_interview_form_email(self):
        """Send exit interview form email to employee"""
        if not self.employee_id.work_email:
            raise ValidationError(_('Employee email address is required to send exit interview form.'))
        
        # Generate security token
        security_token = self._generate_security_token()
        self.write({'security_token': security_token})
        
        # Read HTML template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'email_templates', 'exit_interview_form.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Prepare template variables
        template_vars = {
            'clearance_id': self.id,
            'employee_id': self.employee_id.id,
            'security_token': security_token,
            'interview_date': self.final_interview_date or fields.Date.today(),
            'employee_name': self.employee_id.name,
            'department': f"{self.employee_id.job_id.name or 'N/A'} / {self.employee_id.department_id.name or 'N/A'}",
            'supervisor_name': self.supervisor_name or '',
            'supervisor_title': self.supervisor_title or '',
            'last_working_day': self.last_working_day,
            'length_of_service': self.length_of_service or '',
            'form_submission_url': f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/exit_interview/submit",
        }
        
        # Replace template variables
        for key, value in template_vars.items():
            template_content = template_content.replace(f'${{{key}}}', str(value))
        
        # Create email
        mail_values = {
            'subject': f'Exit Interview Form - {self.employee_id.name}',
            'body_html': template_content,
            'email_to': self.employee_id.work_email,
            'email_from': self.env.user.company_id.email,
            'auto_delete': False,
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        self.write({'exit_interview_form_generated': True})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Exit Interview Form Sent'),
                'message': _('Exit interview form has been sent to %s') % self.employee_id.work_email,
                'type': 'success',
            }
        }
    
    def action_send_department_clearance_emails(self):
        """Send department clearance forms to relevant departments"""
        departments_to_clear = ['HR', 'IT', 'Finance', 'Line Manager']
        
        for department in departments_to_clear:
            # Get department manager
            manager = self._get_department_manager(department)
            if not manager or not manager.work_email:
                continue
            
            # Generate security token
            security_token = self._generate_security_token()
            
            # Read HTML template
            template_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'email_templates', 'department_clearance_form.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Prepare template variables
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            department_id = self._get_department_id(department)
            
            template_vars = {
                'clearance_id': self.id,
                'department': department,
                'department_name': department,
                'manager_id': manager.id,
                'department_id': department_id,
                'security_token': security_token,
                'employee_name': self.employee_id.name,
                'employee_department': self.employee_id.department_id.name or 'N/A',
                'last_working_day': self.last_working_day,
                'clearance_status': 'pending',
                'equipment_list': self.equipment_return_ids,
                'form_submission_url': f"{base_url}/exit-clearance/submit-department",
                'approve_url': f"{base_url}/exit-clearance/approve-department?clearance_id={self.id}&security_token={security_token}&department_id={department_id}",
                'reject_url': f"{base_url}/exit-clearance/reject-department?clearance_id={self.id}&security_token={security_token}&department_id={department_id}",
            }
            
            # Replace template variables
            for key, value in template_vars.items():
                if key == 'equipment_list':
                    # Handle equipment list formatting
                    equipment_html = ''
                    for equipment in value:
                        equipment_html += f'''
                        <tr>
                            <td>{equipment.item_description}</td>
                            <td>{equipment.serial_number or 'N/A'}</td>
                            <td>
                                <select name="equipment_status_{equipment.id}" required>
                                    <option value="">Select Status</option>
                                    <option value="returned">Returned</option>
                                    <option value="not_returned">Not Returned</option>
                                    <option value="damaged">Damaged</option>
                                    <option value="lost">Lost</option>
                                </select>
                            </td>
                            <td>
                                <select name="equipment_condition_{equipment.id}">
                                    <option value="">Select Condition</option>
                                    <option value="excellent">Excellent</option>
                                    <option value="good">Good</option>
                                    <option value="fair">Fair</option>
                                    <option value="poor">Poor</option>
                                    <option value="damaged">Damaged</option>
                                </select>
                            </td>
                            <td>
                                <input type="text" name="equipment_notes_{equipment.id}" placeholder="Notes">
                            </td>
                        </tr>
                        '''
                    template_content = template_content.replace(f'% for equipment in equipment_list:', '')
                    template_content = template_content.replace(f'% endfor', equipment_html)
                elif key == 'department' and value == 'HR':
                    # Handle HR-specific content
                    hr_content = '''
                    <div class="form-group">
                        <label for="hr_records_updated">HR Records Updated:</label>
                        <select id="hr_records_updated" name="hr_records_updated" required>
                            <option value="">Select Status</option>
                            <option value="completed">Completed</option>
                            <option value="pending">Pending</option>
                            <option value="not_applicable">Not Applicable</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="benefits_processed">Benefits Processed:</label>
                        <select id="benefits_processed" name="benefits_processed" required>
                            <option value="">Select Status</option>
                            <option value="completed">Completed</option>
                            <option value="pending">Pending</option>
                            <option value="not_applicable">Not Applicable</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="final_payroll_processed">Final Payroll Processed:</label>
                        <select id="final_payroll_processed" name="final_payroll_processed" required>
                            <option value="">Select Status</option>
                            <option value="completed">Completed</option>
                            <option value="pending">Pending</option>
                            <option value="not_applicable">Not Applicable</option>
                        </select>
                    </div>
                    '''
                    template_content = template_content.replace(f'% if department == \'HR\':', '')
                    template_content = template_content.replace(f'% endif', hr_content)
                else:
                    template_content = template_content.replace(f'${{{key}}}', str(value))
            
            # Create email
            mail_values = {
                'subject': f'Department Clearance Form - {department} - {self.employee_id.name}',
                'body_html': template_content,
                'email_to': manager.work_email,
                'email_from': self.env.user.company_id.email,
                'auto_delete': False,
            }
            
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Department Clearance Forms Sent'),
                'message': _('Department clearance forms have been sent to relevant managers'),
                'type': 'success',
            }
        }
    
    def action_generate_hr_final_form(self):
        """Generate HR final clearance form"""
        # Generate security token
        security_token = self._generate_security_token()
        
        # Read HTML template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'email_templates', 'hr_final_clearance_form.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Prepare template variables
        template_vars = {
            'clearance_id': self.id,
            'security_token': security_token,
            'employee_name': self.employee_id.name,
            'employee_id': self.employee_id.work_email or 'N/A',
            'department': self.employee_id.department_id.name or 'N/A',
            'position': self.employee_id.job_id.name or 'N/A',
            'supervisor_name': self.supervisor_name or 'N/A',
            'length_of_service': self.length_of_service or 'N/A',
            'last_working_day': self.last_working_day,
            'exit_reason': self.exit_reason or 'N/A',
            'interview_date': self.final_interview_date or 'N/A',
            'reason_for_leaving_category': dict(self._fields['reason_for_leaving_category'].selection).get(self.reason_for_leaving_category, 'N/A') if self.reason_for_leaving_category else 'N/A',
            'reason_for_leaving_other': self.reason_for_leaving_other or '',
            'decision_factors': self.decision_factors or 'N/A',
            'most_satisfying': self.most_satisfying or 'N/A',
            'least_satisfying': self.least_satisfying or 'N/A',
            'job_duties_as_expected': self.job_duties_as_expected or 'N/A',
            'improvement_suggestions': self.improvement_suggestions or 'N/A',
            'equipment_returns': self.equipment_return_ids,
            'all_equipment_returned': self.all_equipment_returned,
            'all_cleared': self.all_cleared,
            'total_equipment_count': len(self.equipment_return_ids),
            'returned_equipment_count': len([eq for eq in self.equipment_return_ids if eq.status == 'returned']),
            'pending_equipment_count': len([eq for eq in self.equipment_return_ids if eq.status != 'returned']),
            'grievance_history': self._get_employee_grievance_history(),
            'disciplinary_actions': self._get_employee_disciplinary_actions(),
            'employee_signature': f"data:image/png;base64,{base64.b64encode(self.employee_signature).decode()}" if self.employee_signature else '',
            'employee_signature_date': self.employee_signature_date or 'N/A',
            'hr_supervisor_signature': f"data:image/png;base64,{base64.b64encode(self.hr_supervisor_signature).decode()}" if self.hr_supervisor_signature else '',
            'hr_supervisor_signature_date': self.hr_supervisor_signature_date or 'N/A',
            'final_submission_url': f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/final_clearance/submit",
        }
        
        # Replace template variables
        for key, value in template_vars.items():
            if key in ['equipment_returns', 'grievance_history', 'disciplinary_actions']:
                # Handle list formatting
                if key == 'equipment_returns':
                    equipment_html = ''
                    for equipment in value:
                        equipment_html += f'''
                        <tr>
                            <td>{equipment.item_description}</td>
                            <td>{equipment.serial_number or 'N/A'}</td>
                            <td>{equipment.date_returned or 'N/A'}</td>
                            <td><span class="status-badge status-{equipment.status}">{equipment.status}</span></td>
                            <td>{equipment.condition_on_return or 'N/A'}</td>
                            <td>{equipment.returned_to or 'N/A'}</td>
                            <td>{equipment.notes or 'N/A'}</td>
                        </tr>
                        '''
                    template_content = template_content.replace(f'% for equipment in equipment_returns:', '')
                    template_content = template_content.replace(f'% endfor', equipment_html)
                elif key == 'grievance_history':
                    grievance_html = ''
                    for grievance in value:
                        grievance_html += f'''
                        <tr>
                            <td>{grievance.submission_date or 'N/A'}</td>
                            <td>{grievance.grievance_type or 'N/A'}</td>
                            <td>{grievance.title or 'N/A'}</td>
                            <td><span class="status-badge status-{grievance.status}">{grievance.status}</span></td>
                            <td>{grievance.resolution_notes or 'N/A'}</td>
                        </tr>
                        '''
                    template_content = template_content.replace(f'% for grievance in grievance_history:', '')
                    template_content = template_content.replace(f'% endfor', grievance_html)
                elif key == 'disciplinary_actions':
                    disciplinary_html = ''
                    for action in value:
                        disciplinary_html += f'''
                        <tr>
                            <td>{action.action_date or 'N/A'}</td>
                            <td>{action.action_type or 'N/A'}</td>
                            <td>{action.reason or 'N/A'}</td>
                            <td><span class="status-badge status-{action.severity}">{action.severity}</span></td>
                            <td><span class="status-badge status-{action.status}">{action.status}</span></td>
                        </tr>
                        '''
                    template_content = template_content.replace(f'% for action in disciplinary_actions:', '')
                    template_content = template_content.replace(f'% endfor', disciplinary_html)
            else:
                template_content = template_content.replace(f'${{{key}}}', str(value))
        
        # Create attachment
        attachment_name = f'Final_Clearance_Form_{self.employee_id.name.replace(" ", "_")}_{fields.Date.today()}.html'
        attachment_values = {
            'name': attachment_name,
            'type': 'binary',
            'datas': base64.b64encode(template_content.encode('utf-8')),
            'res_model': 'hr.exit.clearance',
            'res_id': self.id,
            'mimetype': 'text/html',
        }
        
        attachment = self.env['ir.attachment'].create(attachment_values)
        self.write({
            'clearance_form_attachment_id': attachment.id,
            'clearance_form_filename': attachment_name
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    def _get_department_manager(self, department):
        """Get department manager based on department name"""
        # This is a simplified implementation - in practice, you would have proper department-manager relationships
        if department == 'HR':
            return self.env['hr.employee'].search([('job_id.name', 'ilike', 'HR Manager')], limit=1)
        elif department == 'IT':
            return self.env['hr.employee'].search([('job_id.name', 'ilike', 'IT Manager')], limit=1)
        elif department == 'Finance':
            return self.env['hr.employee'].search([('job_id.name', 'ilike', 'Finance Manager')], limit=1)
        elif department == 'Line Manager':
            return self.manager_id
        return None

    def _get_department_id(self, department):
        """Get department ID based on department name"""
        # This is a simplified implementation - in practice, you would have proper department mappings
        if department == 'HR':
            hr_dept = self.env['hr.department'].search([('name', 'ilike', 'Human Resources')], limit=1)
            return hr_dept.id if hr_dept else 1
        elif department == 'IT':
            it_dept = self.env['hr.department'].search([('name', 'ilike', 'Information Technology')], limit=1)
            return it_dept.id if it_dept else 2
        elif department == 'Finance':
            finance_dept = self.env['hr.department'].search([('name', 'ilike', 'Finance')], limit=1)
            return finance_dept.id if finance_dept else 3
        elif department == 'Line Manager':
            return self.employee_id.department_id.id if self.employee_id.department_id else 4
        return 1  # Default fallback

    def _get_employee_grievance_history(self):
        """Get employee grievance history"""
        if not self.employee_id:
            return []
        
        # Search for grievance records related to this employee
        grievances = self.env['hr.grievance'].search([
            ('employee_id', '=', self.employee_id.id)
        ], order='submission_date desc')
        
        return grievances

    def _get_employee_disciplinary_actions(self):
        """Get employee disciplinary actions"""
        if not self.employee_id:
            return []
        
        # Search for disciplinary action records related to this employee
        # Note: This assumes there's a disciplinary action model, adjust as needed
        disciplinary_actions = []
        
        # Try to find disciplinary actions in the system
        # This is a placeholder - you may need to adjust based on your actual model structure
        try:
            # Look for a disciplinary action model if it exists
            disciplinary_model = self.env['hr.disciplinary.action']
            disciplinary_actions = disciplinary_model.search([
                ('employee_id', '=', self.employee_id.id)
            ], order='action_date desc')
        except Exception:
            # If the model doesn't exist, return empty list
            # You can customize this to look for disciplinary data in other models
            pass
        
        return disciplinary_actions


class HrExitClearanceLine(models.Model):
    _name = 'hr.exit.clearance.line'
    _description = 'HR Exit Clearance Line'
    _order = 'sequence'
    
    clearance_id = fields.Many2one('hr.exit.clearance', string='Clearance',
                                  required=True, ondelete='cascade')
    
    department = fields.Selection([
        ('IT', 'IT'),
        ('Sales', 'Sales'),
        ('Marketing', 'Marketing'),
        ('Finance', 'Finance'),
        ('Management', 'Management'),
        ('Customer Service', 'Customer Service')
    ], string='Department Code', required=True)
    
    department_name = fields.Char(string='Department Name', required=True)
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', required=True)
    
    cleared_by = fields.Many2one('res.users', string='Cleared By',
                                readonly=True)
    
    clearance_date = fields.Date(string='Clearance Date',
                                readonly=True)
    
    notes = fields.Text(string='Notes')
    
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    def action_clear(self):
        self.write({
            'status': 'cleared',
            'cleared_by': self.env.user.id,
            'clearance_date': fields.Date.today()
        })
        self._check_all_cleared()
    
    def action_reject(self):
        self.write({'status': 'rejected'})
    
    def action_reset_pending(self):
        self.write({
            'status': 'pending',
            'cleared_by': False,
            'clearance_date': False
        })
    
    def _check_all_cleared(self):
        """Check if all departments are cleared"""
        if all(line.status == 'cleared' for line in self.clearance_id.clearance_line_ids):
            self.clearance_id.action_generate_clearance_form()
    
    def _valid_field_parameter(self, field, name):
        """Override to handle deprecated tracking parameter"""
        if name == 'tracking':
            return True  # Accept but ignore the tracking parameter
        return super()._valid_field_parameter(field, name)
