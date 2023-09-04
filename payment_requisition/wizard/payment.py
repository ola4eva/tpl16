from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PaymentWizard(models.TransientModel):

    _name = 'payment_requisition.register_payment'

    payment_type = fields.Selection(selection=[
        ('full_payment', "Register Full Payment"),
        ('down_payment', "Down Payment"),
    ], required=True)
    requisition_id = fields.Many2one("payment.requisition.form", "Requisition")
    amount = fields.Float("Amount", required=True)
    total_amount_outstanding = fields.Float("Total outstanding", readonly=True)

    @api.constrains('amount', 'total_amount_outstanding')
    def _restrict_amount_to_pay(self):
        if self.amount > self.total_amount_outstanding:
            raise UserError(_("Amount to pay must not be greater than amount outstanding!"))

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.payment_type and self.payment_type == 'full_payment':
            self.amount = self.total_amount_outstanding

    def do_pay(self):
        requisition = self.requisition_id
        payment_type = self.payment_type
        amount = self.amount
        return requisition.action_sheet_move_create(payment_type, amount=amount)
