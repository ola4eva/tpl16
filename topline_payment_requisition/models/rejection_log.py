from odoo import models, fields


class PaymentRequisitionReject(models.Model):
    _name = 'payment.requisition.rejection.log'
    _description = 'Payment Requisition Rejection Log'

    requisition_id = fields.Many2one(
        comodel_name='payment.requisition.form', string='Requisition')
    reason = fields.Char(string='Reason')
    user_id = fields.Many2one(comodel_name='res.users', string='Rejected By')
    datetime_rejection = fields.Datetime('Date')
