from odoo import models, api

class account_payment(models.Model):
    _inherit = "account.payment"

    @api.model_create_multi
    def create(self, vals_list):
        # for vals in vals_list:
        payment = super(account_payment, self).create(vals_list)
        payment.send_payment_creation_mail()
        return payment

    
    def send_payment_creation_mail(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_payment_notification')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "A new payment has been created and needs internal audit review".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False