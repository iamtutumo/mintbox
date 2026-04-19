# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAdvanceLoanPaymentSchedule(models.Model):
    _name = 'surepay_payroll.hr.advance.loan.payment.schedule'
    _description = 'Loan Payment Schedule'
    _order = 'due_date asc'

    loan_id = fields.Many2one(
        'surepay_payroll.hr.loan',
        string='Loan',
        required=True,
        ondelete='cascade',
        help='Related loan'
    )
    installment_number = fields.Integer(
        string='Installment Number',
        required=True,
        help='Sequence number of this installment'
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        help='Date when this installment is due'
    )
    amount = fields.Float(
        string='Amount',
        required=True,
        help='Amount due for this installment'
    )
    principal_amount = fields.Float(
        string='Principal Amount',
        required=True,
        help='Principal portion of this installment'
    )
    interest_amount = fields.Float(
        string='Interest Amount',
        default=0.0,
        help='Interest portion of this installment'
    )
    status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived')
    ], string='Status', default='pending', required=True, help='Payment status')
    payment_date = fields.Date(
        string='Payment Date',
        help='Date when this installment was paid'
    )
    paid_amount = fields.Float(
        string='Paid Amount',
        default=0.0,
        help='Actual amount paid'
    )
    notes = fields.Text(
        string='Notes',
        help='Additional notes for this installment'
    )

    @api.constrains('amount', 'principal_amount', 'interest_amount')
    def _check_amounts(self):
        for schedule in self:
            if schedule.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))
            if schedule.principal_amount < 0:
                raise ValidationError(_('Principal amount cannot be negative.'))
            if schedule.interest_amount < 0:
                raise ValidationError(_('Interest amount cannot be negative.'))
            # Check that amount equals principal + interest
            if not schedule.currency_id.is_zero(schedule.amount - (schedule.principal_amount + schedule.interest_amount)):
                raise ValidationError(_('Amount must equal principal plus interest.'))

    @api.constrains('payment_date', 'status')
    def _check_payment_date(self):
        for schedule in self:
            if schedule.status == 'paid' and not schedule.payment_date:
                raise ValidationError(_('Payment date is required for paid installments.'))
            if schedule.status == 'pending' and schedule.payment_date:
                raise ValidationError(_('Payment date should not be set for pending installments.'))

    def action_mark_paid(self, amount=None):
        """Mark installment as paid"""
        self.write({
            'status': 'paid',
            'payment_date': fields.Date.today(),
            'paid_amount': amount or self.amount
        })

    def action_mark_overdue(self):
        """Mark installment as overdue"""
        self.write({'status': 'overdue'})

    def action_waive(self, reason=None):
        """Waive this installment"""
        self.write({
            'status': 'waived',
            'notes': reason or self.notes
        })

    @api.model
    def _check_overdue_installments(self):
        """Cron job to check and mark overdue installments"""
        today = fields.Date.today()
        overdue_schedules = self.search([
            ('status', '=', 'pending'),
            ('due_date', '<', today)
        ])
        overdue_schedules.action_mark_overdue()
        return True
