# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.tools import float_compare


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_requisition_id = fields.Many2one(
        'payment.requisition.form', string='Payment Requisition', copy=False, help="Payment Requisition where the move line come from")

    def reconcile(self):
        res = super(AccountMoveLine, self).reconcile()
        account_move_ids = [l.move_id.id for l in self]
        if account_move_ids:
            expense_sheets = self.env['hr.expense.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            expense_sheets.set_to_paid()
        return res
