from datetime import datetime
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class RejectRequisition(models.TransientModel):

    _name = 'reject.payment.requisition'
    _description = 'Reject Payment Requisition'

    requisition_id = fields.Many2one(
        comodel_name='payment.requisition.form', string="Requisition")
    reject_reason = fields.Char(string='Reason')
    user_id = fields.Many2one(comodel_name='res.users', string='User')

    def log_reason(self):
        """
        This logs the reason why this payment requisition was rejected.
        """
        RejectionLog = self.env['payment.requisition.rejection.log'].sudo()
        values = {
            'requisition_id': self.requisition_id.id,
            'reason': self.reject_reason,
            'user_id': self.env.uid,
            'datetime_rejection': datetime.now()
        }
        try:
            log = RejectionLog.create(values)
            print("&&&&&&& Log &&&&&&&&&&", log)
        except Exception as e:
            _logger.error("Error logging payment requisition rejection reason\n%s" % e)
        return self.requisition_id.sudo().write({'state': 'reject'})
