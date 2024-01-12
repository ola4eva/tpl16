from odoo import models, fields


class AccountJournal(models.Model):

    _inherit = 'account.move'

    requisition_id = fields.Many2one(
        "payment.requisition.form", "Payment Requisition")

    def action_post(self):
        res = super(AccountJournal, self).action_post()
        if self.requisition_id:
            requisition = self.env['payment.requisition.form'].search(
                [('payment_ids', 'in', [self.id])], limit=1)
            if not requisition:
                requisition = self.requisition_id
            if requisition:
                requisition._confirm_post()
        return res
