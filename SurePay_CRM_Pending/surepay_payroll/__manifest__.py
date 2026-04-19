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
{
    'name': 'SurePay Payroll',
    'version': '17.0.1.0.1',
    'category': 'Human Resources',
    'summary': 'Multi-country Payroll System with statutory compliance and advance management',
    'description': "Comprehensive Payroll Management System with multi-country support, statutory compliance, "
                   "and advanced features including salary advance management. Features include automated payroll processing, "
                   "flexible tax calculations, detailed reporting, "
                   "and configurable salary structures for Ugandan businesses with multi-company capabilities.",
    'author': 'SurePay Ltd',
    'company': 'SurePay Ltd',
    'maintainer': 'SurePay Ltd',
    'website': 'https://surepayltd.com',
    'depends': ['hr_contract', 'hr_holidays', 'base', 'account'],
    'external_dependencies': {'python': []},
    'application': True,
    'installable': True,
    'auto_install': False,
    'data': [
        'security/hr_payroll_security.xml',
        'security/ir.model.access.csv',
        'data/hr_payroll_sequence.xml',
        'data/hr_payroll_data.xml',
        'data/hr_payroll_surepay_data.xml',
        'wizard/hr_payslips_employees_views.xml',
        'wizard/payslip_lines_contribution_register_views.xml',
        'report/hr_payroll_report.xml',
        'report/report_contribution_register_templates.xml',
        'report/report_payslip_templates.xml',
        'report/report_payslip_details_templates.xml',
        'report/report_payslip_surepay_templates.xml',
        'static/src/xml/payroll_assets.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_salary_rule_views.xml',
        'views/hr_salary_rule_category_views.xml',
        'views/hr_contribution_register_views.xml',
        'views/hr_payroll_structure_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_payslip_line_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_payslip_run_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_salary_advance_simple_views.xml',
        'views/hr_loan_views.xml',
        'views/hr_payroll_menu.xml',
        'views/hr_advance_loan_report_views.xml',

    ],
    'demo': ['data/hr_payroll_demo.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
