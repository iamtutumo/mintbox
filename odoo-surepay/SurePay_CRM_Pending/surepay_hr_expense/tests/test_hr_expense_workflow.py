# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class TestHrExpenseWorkflow(common.TransactionCase):

    def setUp(self):
        super(TestHrExpenseWorkflow, self).setUp()
        
        # Create test employee
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'work_email': 'test.employee@example.com',
        })
        
        # Create test manager
        self.manager = self.env['hr.employee'].create({
            'name': 'Test Manager',
            'work_email': 'test.manager@example.com',
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
        })
        self.budget.action_activate()
        
        # Create test expense
        self.expense = self.env['hr.expense'].create({
            'name': 'Test Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 100.0,
            'quantity': 2.0,
            'budget_id': self.budget.id,
        })

    def test_expense_creation(self):
        """Test expense creation and basic fields"""
        self.assertEqual(self.expense.employee_id, self.employee)
        self.assertEqual(self.expense.product_id, self.product)
        self.assertEqual(self.expense.unit_amount, 100.0)
        self.assertEqual(self.expense.quantity, 2.0)
        self.assertEqual(self.expense.total_amount, 200.0)
        self.assertEqual(self.expense.budget_id, self.budget)
        self.assertEqual(self.expense.approval_level, 'standard')

    def test_expense_budget_validation(self):
        """Test expense budget validation"""
        # Test valid budget
        is_valid, message = self.expense.validate_budget()
        self.assertTrue(is_valid)
        
        # Test expense exceeding budget
        large_expense = self.env['hr.expense'].create({
            'name': 'Large Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 1500.0,
            'quantity': 1.0,
            'budget_id': self.budget.id,
        })
        
        is_valid, message = large_expense.validate_budget()
        self.assertFalse(is_valid)
        self.assertIn('exceeds', message.lower())

    def test_expense_approval_workflow(self):
        """Test expense approval workflow"""
        # Submit expense
        self.expense.action_submit_sheet()
        self.assertEqual(self.expense.state, 'submit')
        
        # Approve expense
        self.expense.approve_expense_sheets()
        self.assertEqual(self.expense.state, 'approve')
        
        # Post expense
        self.expense.action_sheet_move_create()
        self.assertEqual(self.expense.state, 'post')
        
        # Check budget impact
        self.budget._compute_amount_spent()
        self.assertEqual(self.budget.amount_spent, 200.0)
        self.assertEqual(self.budget.amount_remaining, 800.0)

    def test_expense_override_request(self):
        """Test expense override request workflow"""
        # Create expense that exceeds budget
        override_expense = self.env['hr.expense'].create({
            'name': 'Override Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 1200.0,
            'quantity': 1.0,
            'budget_id': self.budget.id,
        })
        
        # Submit expense
        override_expense.action_submit_sheet()
        
        # Request override
        override_expense.request_override(self.manager.id, 'Budget override needed for urgent expense')
        self.assertEqual(override_expense.approval_level, 'override')
        self.assertEqual(override_expense.override_requested_by, self.employee)
        self.assertEqual(override_expense.override_requested_to, self.manager)
        
        # Approve override
        override_expense.approve_override()
        self.assertEqual(override_expense.approval_level, 'approved')
        self.assertEqual(override_expense.state, 'approve')

    def test_expense_escalation_workflow(self):
        """Test expense escalation workflow"""
        # Create expense that needs escalation
        escalation_expense = self.env['hr.expense'].create({
            'name': 'Escalation Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 2000.0,
            'quantity': 1.0,
            'budget_id': self.budget.id,
        })
        
        # Submit expense
        escalation_expense.action_submit_sheet()
        
        # Request escalation
        escalation_expense.request_escalation(self.manager.id, 'High value expense requires director approval')
        self.assertEqual(escalation_expense.approval_level, 'escalated')
        self.assertEqual(escalation_expense.escalation_requested_by, self.employee)
        self.assertEqual(escalation_expense.escalation_requested_to, self.manager)
        
        # Approve escalation
        escalation_expense.approve_escalation()
        self.assertEqual(escalation_expense.approval_level, 'approved')
        self.assertEqual(escalation_expense.state, 'approve')

    def test_expense_rejection(self):
        """Test expense rejection workflow"""
        # Submit expense
        self.expense.action_submit_sheet()
        
        # Reject expense
        self.expense.refuse_expense_sheet('Expense rejected due to policy violation')
        self.assertEqual(self.expense.state, 'cancel')
        
        # Check budget impact (should be none)
        self.budget._compute_amount_spent()
        self.assertEqual(self.budget.amount_spent, 0.0)

    def test_expense_budget_tracking(self):
        """Test expense budget tracking and updates"""
        # Create multiple expenses
        expense1 = self.env['hr.expense'].create({
            'name': 'Expense 1',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 100.0,
            'quantity': 1.0,
            'budget_id': self.budget.id,
        })
        
        expense2 = self.env['hr.expense'].create({
            'name': 'Expense 2',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 200.0,
            'quantity': 1.0,
            'budget_id': self.budget.id,
        })
        
        # Submit and approve expenses
        expense1.action_submit_sheet()
        expense1.approve_expense_sheets()
        
        expense2.action_submit_sheet()
        expense2.approve_expense_sheets()
        
        # Check budget tracking
        self.budget._compute_amount_spent()
        self.assertEqual(self.budget.amount_spent, 300.0)
        self.assertEqual(self.budget.amount_remaining, 700.0)
        self.assertEqual(self.budget.expense_count, 2)

    def test_expense_without_budget(self):
        """Test expense creation without budget"""
        expense_no_budget = self.env['hr.expense'].create({
            'name': 'Expense Without Budget',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 50.0,
            'quantity': 1.0,
        })
        
        self.assertFalse(expense_no_budget.budget_id)
        
        # Should still be able to submit and approve
        expense_no_budget.action_submit_sheet()
        expense_no_budget.approve_expense_sheets()
        self.assertEqual(expense_no_budget.state, 'approve')

    def test_expense_workflow_permissions(self):
        """Test expense workflow permissions"""
        # Create another user
        other_user = self.env['res.users'].create({
            'name': 'Other User',
            'login': 'other.user@example.com',
            'email': 'other.user@example.com',
        })
        
        # Create expense as other user
        other_expense = self.env['hr.expense'].with_user(other_user).create({
            'name': 'Other User Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 50.0,
            'quantity': 1.0,
            'budget_id': self.budget.id,
        })
        
        # Test that original user cannot modify other user's expense
        with self.assertRaises(UserError):
            other_expense.with_user(self.env.user).action_submit_sheet()

    def test_expense_budget_period_validation(self):
        """Test expense validation against budget period"""
        # Create expired budget
        expired_budget = self.env['hr.expense.budget'].create({
            'employee_id': self.employee.id,
            'period_type': 'month',
            'amount_allocated': 500.0,
            'date_start': datetime.now() - timedelta(days=60),
            'date_end': datetime.now() - timedelta(days=30),
        })
        expired_budget.action_activate()
        expired_budget.action_expire()
        
        # Create expense with expired budget
        expired_expense = self.env['hr.expense'].create({
            'name': 'Expired Budget Expense',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 50.0,
            'quantity': 1.0,
            'budget_id': expired_budget.id,
        })
        
        # Should fail validation
        is_valid, message = expired_expense.validate_budget()
        self.assertFalse(is_valid)
        self.assertIn('expired', message.lower())

    def test_expense_notification_workflow(self):
        """Test expense notification workflow"""
        # Test that notifications are sent during approval process
        with self.mock_mail_gateway():
            # Submit expense
            self.expense.action_submit_sheet()
            
            # Approve expense
            self.expense.approve_expense_sheets()
            
            # Check that notifications were sent
            messages = self.env['mail.message'].search([
                ('model', '=', 'hr.expense'),
                ('res_id', '=', self.expense.id),
            ])
            self.assertTrue(len(messages) > 0)
