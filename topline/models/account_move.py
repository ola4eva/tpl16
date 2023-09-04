# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_requisition_id = fields.Many2one(
        'payment.requisition.form', string='Payment Requisition', copy=False, help="Payment Requisition where the move line come from")

    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(AccountMoveLine, self).reconcile(
            writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        account_move_ids = [l.move_id.id for l in self if float_compare(
            l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        if account_move_ids:
            expense_sheets = self.env['hr.expense.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            expense_sheets.set_to_paid()
        return res
