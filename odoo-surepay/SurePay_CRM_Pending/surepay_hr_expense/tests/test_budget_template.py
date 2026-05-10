# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class TestBudgetTemplate(common.TransactionCase):

    def setUp(self):
        super(TestBudgetTemplate, self).setUp()
        
        # Create test employees
        self.employee1 = self.env['hr.employee'].create({
            'name': 'Test Employee 1',
            'work_email': 'test1.employee@example.com',
        })
        
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Test Employee 2',
            'work_email': 'test2.employee@example.com',
        })
        
        # Create test department
        self.department = self.env['hr.department'].create({
            'name': 'Test Department',
            'manager_id': self.employee1.id,
        })
        
        # Create test job position
        self.job = self.env['hr.job'].create({
            'name': 'Test Job Position',
            'department_id': self.department.id,
        })
        
        # Assign employees to department and job
        self.employee1.write({
            'department_id': self.department.id,
            'job_id': self.job.id,
        })
        
        self.employee2.write({
            'department_id': self.department.id,
            'job_id': self.job.id,
        })
        
        # Create test budget template
        self.template = self.env['hr.expense.budget.template'].create({
            'name': 'Monthly Budget Template',
            'description': 'Standard monthly budget for employees',
            'period_type': 'month',
            'amount_allocated': 1000.0,
            'auto_renew': True,
            'rollover_remaining': True,
        })

    def test_template_creation(self):
        """Test budget template creation and basic fields"""
        self.assertEqual(self.template.name, 'Monthly Budget Template')
        self.assertEqual(self.template.period_type, 'month')
        self.assertEqual(self.template.amount_allocated, 1000.0)
        self.assertTrue(self.template.auto_renew)
        self.assertTrue(self.template.rollover_remaining)
        self.assertTrue(self.template.active)

    def test_template_employee_applicability(self):
        """Test template employee applicability"""
        # Add specific employees to template
        self.template.write({
            'employee_ids': [(6, 0, [self.employee1.id])],
        })
        
        self.assertIn(self.employee1, self.template.employee_ids)
        self.assertNotIn(self.employee2, self.template.employee_ids)
        
        # Test applicable employees
        applicable_employees = self.template.get_applicable_employees()
        self.assertIn(self.employee1, applicable_employees)
        self.assertNotIn(self.employee2, applicable_employees)

    def test_template_department_applicability(self):
        """Test template department applicability"""
        # Add department to template
        self.template.write({
            'department_ids': [(6, 0, [self.department.id])],
        })
        
        self.assertIn(self.department, self.template.department_ids)
        
        # Test applicable employees
        applicable_employees = self.template.get_applicable_employees()
        self.assertIn(self.employee1, applicable_employees)
        self.assertIn(self.employee2, applicable_employees)

    def test_template_job_applicability(self):
        """Test template job position applicability"""
        # Add job position to template
        self.template.write({
            'job_ids': [(6, 0, [self.job.id])],
        })
        
        self.assertIn(self.job, self.template.job_ids)
        
        # Test applicable employees
        applicable_employees = self.template.get_applicable_employees()
        self.assertIn(self.employee1, applicable_employees)
        self.assertIn(self.employee2, applicable_employees)

    def test_template_no_filters(self):
        """Test template with no filters (applies to all employees)"""
        # Template with no filters should apply to all active employees
        applicable_employees = self.template.get_applicable_employees()
        self.assertIn(self.employee1, applicable_employees)
        self.assertIn(self.employee2, applicable_employees)

    def test_template_budget_creation(self):
        """Test budget creation from template"""
        # Create budgets from template
        budgets = self.template.create_budgets_from_template()
        
        self.assertTrue(len(budgets) > 0)
        
        # Check created budgets
        for budget in budgets:
            self.assertEqual(budget.employee_id.company_id, self.template.company_id)
            self.assertEqual(budget.period_type, self.template.period_type)
            self.assertEqual(budget.amount_allocated, self.template.amount_allocated)
            self.assertEqual(budget.auto_renew, self.template.auto_renew)
            self.assertEqual(budget.rollover_remaining, self.template.rollover_remaining)
            self.assertEqual(budget.budget_template_id, self.template)

    def test_template_duplicate_prevention(self):
        """Test that template doesn't create duplicate budgets"""
        # Create initial budgets
        self.template.create_budgets_from_template()
        
        # Try to create budgets again
        budgets = self.template.create_budgets_from_template()
        
        # Should return empty list as budgets already exist
        self.assertEqual(len(budgets), 0)

    def test_template_budget_count(self):
        """Test template budget count computation"""
        # Initially no budgets
        self.assertEqual(self.template.budget_count, 0)
        
        # Create budgets
        self.template.create_budgets_from_template()
        
        # Check budget count
        self.template._compute_budget_count()
        self.assertGreater(self.template.budget_count, 0)

    def test_template_view_budgets(self):
        """Test template view budgets action"""
        # Create budgets
        self.template.create_budgets_from_template()
        
        # Test view budgets action
        action = self.template.action_view_budgets()
        
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'hr.expense.budget')
        self.assertEqual(action['view_mode'], 'tree,form')
        self.assertIn('domain', action)

    def test_template_active_state(self):
        """Test template active state"""
        # Deactivate template
        self.template.active = False
        self.assertFalse(self.template.active)
        
        # Reactivate template
        self.template.active = True
        self.assertTrue(self.template.active)

    def test_template_company_restriction(self):
        """Test template company restriction"""
        # Create another company
        other_company = self.env['res.company'].create({
            'name': 'Other Company',
        })
        
        # Create employee in other company
        other_employee = self.env['hr.employee'].create({
            'name': 'Other Company Employee',
            'work_email': 'other.employee@example.com',
            'company_id': other_company.id,
        })
        
        # Template should only apply to employees in same company
        applicable_employees = self.template.get_applicable_employees()
        self.assertNotIn(other_employee, applicable_employees)

    def test_template_period_types(self):
        """Test template with different period types"""
        period_types = ['week', 'month', 'quarter', 'year', 'custom']
        
        for period_type in period_types:
            template = self.env['hr.expense.budget.template'].create({
                'name': f'{period_type.title()} Template',
                'period_type': period_type,
                'amount_allocated': 500.0,
            })
            
            self.assertEqual(template.period_type, period_type)
            
            # Create budget and check period type
            budgets = template.create_budgets_from_template()
            if budgets:
                budget = budgets[0]
                self.assertEqual(budget.period_type, period_type)

    def test_template_rollover_settings(self):
        """Test template rollover settings"""
        # Test template without rollover
        template_no_rollover = self.env['hr.expense.budget.template'].create({
            'name': 'No Rollover Template',
            'period_type': 'month',
            'amount_allocated': 1000.0,
            'auto_renew': True,
            'rollover_remaining': False,
        })
        
        budgets = template_no_rollover.create_budgets_from_template()
        if budgets:
            budget = budgets[0]
            self.assertFalse(budget.rollover_remaining)

    def test_template_auto_renew_settings(self):
        """Test template auto-renew settings"""
        # Test template without auto-renew
        template_no_renew = self.env['hr.expense.budget.template'].create({
            'name': 'No Auto Renew Template',
            'period_type': 'month',
            'amount_allocated': 1000.0,
            'auto_renew': False,
            'rollover_remaining': True,
        })
        
        budgets = template_no_renew.create_budgets_from_template()
        if budgets:
            budget = budgets[0]
            self.assertFalse(budget.auto_renew)

    def test_template_currency_handling(self):
        """Test template currency handling"""
        company = self.env.company
        self.assertEqual(self.template.currency_id, company.currency_id)
        
        # Test with different currency if multi-currency is enabled
        if self.env['res.currency'].search_count([('id', '!=', company.currency_id.id)]) > 0:
            other_currency = self.env['res.currency'].search([('id', '!=', company.currency_id.id)], limit=1)
            template_with_currency = self.env['hr.expense.budget.template'].create({
                'name': 'Other Currency Template',
                'period_type': 'month',
                'amount_allocated': 1000.0,
                'currency_id': other_currency.id,
            })
            self.assertEqual(template_with_currency.currency_id, other_currency)

    def test_template_budget_relationship(self):
        """Test template and budget relationship"""
        # Create budgets from template
        self.template.create_budgets_from_template()
        
        # Check template budget_ids field
        self.assertGreater(len(self.template.budget_ids), 0)
        
        # Check that budgets reference the template
        for budget in self.template.budget_ids:
            self.assertEqual(budget.budget_template_id, self.template)

    def test_template_validation(self):
        """Test template validation constraints"""
        # Test template without name
        with self.assertRaises(ValidationError):
            self.env['hr.expense.budget.template'].create({
                'name': False,
                'period_type': 'month',
                'amount_allocated': 1000.0,
            })
        
        # Test template without period type
        with self.assertRaises(ValidationError):
            self.env['hr.expense.budget.template'].create({
                'name': 'Test Template',
                'period_type': False,
                'amount_allocated': 1000.0,
            })
        
        # Test template with negative amount
        with self.assertRaises(ValidationError):
            self.env['hr.expense.budget.template'].create({
                'name': 'Test Template',
                'period_type': 'month',
                'amount_allocated': -100.0,
            })
