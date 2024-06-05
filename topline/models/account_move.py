from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        payment = self.env['payment.requisition.form'].search(
            [('name', '=', self.ref)])
        if payment:
            payment.write({'state': 'post'})
        return super(AccountMove, self).action_post()