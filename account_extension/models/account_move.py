from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_distribution = fields.Json(required=True)
