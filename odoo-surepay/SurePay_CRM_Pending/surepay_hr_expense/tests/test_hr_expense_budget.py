# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class TestHrExpenseBudget(common.TransactionCase):

    def setUp(self):
        super(TestHrExpenseBudget, self).setUp()
        
        # Create test employee
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'work_email': 'test.employee@example.com',
        })
        
        # Create test department
        self.department = self.env['hr.department'].create({
            'name': 'Test Department',
        })
        
        # Create test job position
        self.job = self.env['hr.job'].create({
            'name': 'Test Job Position',
        })
        
        # Create test product
        self.product = self.env['product.product'].create({
            'name': 'Test Expense Product',
            'can_be_expensed': True,
            'standard_price': 10.0,
        })
        
        # Create test budget
        self.budget = self.env['hr.expense.budget'].create({
            'employee_id': self.employee.id,
            'period_type': 'month',
            'amount_allocated': 1000.0,
            'date_start': datetime.now().replace(day=1),
            'date_end': (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        })

    def test_budget_creation(self):
        """Test budget creation and basic fields"""
        self.assertEqual(self.budget.employee_id, self.employee)
        self.assertEqual(self.budget.period_type, 'month')
        self.assertEqual(self.budget.amount_allocated, 1000.0)
        self.assertEqual(self.budget.state, 'draft')
        self.assertEqual(self.budget.amount_spent, 0.0)
        self.assertEqual(self.budget.amount_remaining, 1000.0)

    def test_budget_period_calculation(self):
        """Test period date calculations for different period types"""
        # Test weekly period
        week_budget = self.env['hr.expense.budget'].create({
            'employee_id': self.employee.id,
            'period_type': 'week',
            'amount_allocated': 250.0,
        })
        self.assertTrue(week_budget.date_start)
        self.assertTrue(week_budget.date_end)
        self.assertEqual((week_budget.date_end - week_budget.date_start).days, 6)
        
        # Test quarterly period
        quarter_budget = self.env['hr.expense.budget'].create({
            'employee_id': self.employee.id,
            'period_type': 'quarter',
            'amount_allocated': 3000.0,
        })
        self.assertTrue(quarter_budget.date_start)
        self.assertTrue(quarter_budget.date_end)
        
        # Test yearly period
        year_budget = self.env['hr.expense.budget'].create({
            'employee_id': self.employee.id,
            'period_type': 'year',
            'amount_allocated': 12000.0,
        })
        self.assertTrue(year_budget.date_start)
        self.assertTrue(year_budget.date_end)
        self.assertEqual(year_budget.date_start.year, year_budget.date_end.year)

    def test_budget_state_transitions(self):
        """Test budget state transitions"""
        # Activate budget
        self.budget.action_activate()
        self.assertEqual(self.budget.state, 'active')
        
        # Expire budget
        self.budget.action_expire()
        self.assertEqual(self.budget.state, 'expired')
        
        # Set to draft
        self.budget.action_draft()
        self.assertEqual(self.budget.state, 'draft')
        
        # Cancel budget
        self.budget.action_cancel()
        self.assertEqual(self.budget.state, 'cancelled')

    def test_budget_utilization(self):
        """Test budget utilization calculation"""
        self.assertEqual(self.budget.budget_utilization, 0.0)
        
        # Activate budget
        self.budget.action_activate()
        
        # Create expense
        expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 100.0,
            'quantity': 2.0,
            'budget_id': self.budget.id,
        })
        
        # Submit expense
        expense.action_submit_sheet()
        
        # Approve expense
        expense.approve_expense_sheets()
        
        # Check budget utilization
        self.budget._compute_amount_spent()
        self.assertEqual(self.budget.amount_spent, 200.0)
        self.assertEqual(self.budget.amount_remaining, 800.0)
        self.assertEqual(self.budget.budget_utilization, 20.0)

    def test_budget_availability_check(self):
        """Test budget availability for expense submission"""
        # Activate budget
        self.budget.action_activate()
        
        # Check availability
        is_available, message = self.budget.check_budget_availability(500.0)
        self.assertTrue(is_available)
        
        # Check insufficient budget
        is_available, message = self.budget.check_budget_availability(1500.0)
        self.assertFalse(is_available)
        self.assertIn('insufficient', message.lower())

    def test_budget_auto_renewal(self):
        """Test budget auto-renewal functionality"""
        # Create budget with auto-renewal
        auto_renew_budget = self.env['hr.expense.budget'].create({
            'employee_id': self.employee.id,
            'period_type': 'month',
            'amount_allocated': 1000.0,
            'auto_renew': True,
            'rollover_remaining': True,
            'date_start': datetime.now().replace(day=1) - timedelta(days=60),
            'date_end': datetime.now().replace(day=1) - timedelta(days=30),
        })
        
        # Activate budget
        auto_renew_budget.action_activate()
        
        # Add some expenses to test rollover
        expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 100.0,
            'quantity': 3.0,
            'budget_id': auto_renew_budget.id,
        })
        expense.action_submit_sheet()
        expense.approve_expense_sheets()
        
        # Test renewal creation
        renewal_budget = auto_renew_budget.create_renewal_budget()
        self.assertTrue(renewal_budget)
        self.assertEqual(renewal_budget.parent_budget_id, auto_renew_budget)
        self.assertEqual(renewal_budget.employee_id, auto_renew_budget.employee_id)
        self.assertEqual(renewal_budget.period_type, auto_renew_budget.period_type)
        
        # Test rollover
        if auto_renew_budget.rollover_remaining:
            self.assertEqual(renewal_budget.amount_allocated, 1000.0 + 700.0)  # Original + rollover

    def test_budget_child_relationships(self):
        """Test parent-child budget relationships"""
        # Create parent budget
        parent_budget = self.env['hr.expense.budget'].create({
            'employee_id': self.employee.id,
            'period_type': 'year',
            'amount_allocated': 12000.0,
            'auto_renew': True,
        })
        
        # Create child budget
        child_budget = self.env['hr.expense.budget'].create({
            'employee_id': self.employee.id,
            'period_type': 'month',
            'amount_allocated': 1000.0,
            'parent_budget_id': parent_budget.id,
        })
        
        self.assertEqual(child_budget.parent_budget_id, parent_budget)
        self.assertIn(child_budget, parent_budget.child_budget_ids)

    def test_budget_constraints(self):
        """Test budget constraints and validations"""
        # Test overlapping budgets
        with self.assertRaises(ValidationError):
            self.env['hr.expense.budget'].create({
                'employee_id': self.employee.id,
                'period_type': 'month',
                'amount_allocated': 500.0,
                'date_start': self.budget.date_start,
                'date_end': self.budget.date_end,
            })

    def test_budget_expense_relationship(self):
        """Test budget and expense relationship"""
        # Activate budget
        self.budget.action_activate()
        
        # Create expense
        expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 50.0,
            'quantity': 2.0,
            'budget_id': self.budget.id,
        })
        
        self.assertEqual(expense.budget_id, self.budget)
        self.assertIn(expense, self.budget.expense_ids)
        
        # Test expense count
        self.assertEqual(self.budget.expense_count, 1)

    def test_budget_company_currency(self):
        """Test budget currency handling"""
        company = self.env.company
        self.assertEqual(self.budget.currency_id, company.currency_id)
        
        # Test with different currency if multi-currency is enabled
        if self.env['res.currency'].search_count([('id', '!=', company.currency_id.id)]) > 0:
            other_currency = self.env['res.currency'].search([('id', '!=', company.currency_id.id)], limit=1)
            budget_with_currency = self.env['hr.expense.budget'].create({
                'employee_id': self.employee.id,
                'period_type': 'month',
                'amount_allocated': 1000.0,
                'currency_id': other_currency.id,
            })
            self.assertEqual(budget_with_currency.currency_id, other_currency)
