# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _


class HrEmployee(models.Model):
    """Inherit hr_employee for getting Payslip Counts"""
    _inherit = 'hr.employee'
    _description = 'Employee'

    slip_ids = fields.One2many('surepay_payroll.hr.payslip',
                               'employee_id', string='Payslips',
                               readonly=True,
                               help="Choose Payslip for Employee")
    payslip_count = fields.Integer(compute='_compute_payslip_count',
                                   string='Payslip Count',
                                   help="Set Payslip Count")
    
    # Salary Advance & Loan Management
    advance_ids = fields.One2many('surepay_payroll.hr.salary.advance',
                                 'employee_id', string='Salary Advances',
                                 readonly=True,
                                 help="Salary advances for employee")
    loan_ids = fields.One2many('surepay_payroll.hr.loan',
                              'employee_id', string='Employee Loans',
                              readonly=True,
                              help="Employee loans")
    advance_count = fields.Integer(compute='_compute_advance_count',
                                  string='Advance Count',
                                  store=True,
                                  help="Count of salary advances")
    loan_count = fields.Integer(compute='_compute_loan_count',
                               string='Loan Count',
                               store=True,
                               help="Count of employee loans")
    total_advance_outstanding = fields.Float(compute='_compute_total_advance_outstanding',
                                           string='Total Outstanding Advances',
                                           store=True,
                                           help="Total outstanding advance balance")
    total_loan_outstanding = fields.Float(compute='_compute_total_loan_outstanding',
                                        string='Total Outstanding Loans',
                                        store=True,
                                        help="Total outstanding loan balance")
    
    # Uganda Payroll Specific Fields
    lst_amount = fields.Float(string='Local Service Tax',
                             help='Local Service Tax amount for this employee')
    advance_amount = fields.Float(string='Salary Advance',
                                 help='Monthly salary advance deduction amount')
    loan_amount = fields.Float(string='Loan Deduction',
                              help='Monthly loan repayment deduction amount')
    other_deductions = fields.Float(string='Other Deductions',
                                   help='Other monthly deductions amount')
    nssf_number = fields.Char(string='NSSF Number',
                             help='National Social Security Fund number')
    tin_number = fields.Char(string='TIN Number',
                            help='Tax Identification Number')
    payroll_country = fields.Selection([
        ('ug', 'Uganda'),
        ('ke', 'Kenya'),
        ('tz', 'Tanzania'),
        ('rw', 'Rwanda'),
        ('other', 'Other')
    ], string='Payroll Country', default='ug',
       help='Country for payroll calculation rules')

    def _compute_payslip_count(self):
        """Function for count Payslips"""
        payslip_data = self.env['surepay_payroll.hr.payslip'].sudo().read_group(
            [('employee_id', 'in', self.ids)],
            ['employee_id'], ['employee_id'])
        result = dict(
            (data['employee_id'][0], data['employee_id_count']) for data in
            payslip_data)
        for employee in self:
            employee.payslip_count = result.get(employee.id, 0)
    
    def _compute_advance_count(self):
        """Function for count Salary Advances"""
        advance_data = self.env['surepay_payroll.hr.salary.advance'].sudo().read_group(
            [('employee_id', 'in', self.ids)],
            ['employee_id'], ['employee_id'])
        result = dict(
            (data['employee_id'][0], data['employee_id_count']) for data in
            advance_data)
        for employee in self:
            employee.advance_count = result.get(employee.id, 0)
    
    def _compute_loan_count(self):
        """Function for count Employee Loans"""
        loan_data = self.env['surepay_payroll.hr.loan'].sudo().read_group(
            [('employee_id', 'in', self.ids)],
            ['employee_id'], ['employee_id'])
        result = dict(
            (data['employee_id'][0], data['employee_id_count']) for data in
            loan_data)
        for employee in self:
            employee.loan_count = result.get(employee.id, 0)
    
    def _compute_total_advance_outstanding(self):
        """Function for total outstanding advances"""
        for employee in self:
            advances = self.env['surepay_payroll.hr.salary.advance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('status', 'in', ['approved', 'active']),
                ('outstanding_balance', '>', 0)
            ])
            employee.total_advance_outstanding = sum(advances.mapped('outstanding_balance'))
    
    def _compute_total_loan_outstanding(self):
        """Function for total outstanding loans"""
        for employee in self:
            loans = self.env['surepay_payroll.hr.loan'].sudo().search([
                ('employee_id', '=', employee.id),
                ('status', 'in', ['approved', 'active']),
                ('outstanding_balance', '>', 0)
            ])
            employee.total_loan_outstanding = sum(loans.mapped('outstanding_balance'))
    
    def action_view_advances(self):
        """Open salary advances view"""
        self.ensure_one()
        action = {
            'name': _('Salary Advances'),
            'type': 'ir.actions.act_window',
            'res_model': 'surepay_payroll.hr.salary.advance',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
        if self.advance_count == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.advance_ids[0].id,
            })
        return action
    
    def action_view_loans(self):
        """Open employee loans view"""
        self.ensure_one()
        action = {
            'name': _('Employee Loans'),
            'type': 'ir.actions.act_window',
            'res_model': 'surepay_payroll.hr.loan',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
        if self.loan_count == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.loan_ids[0].id,
            })
        return action
