from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.move'
    report_notes = fields.Char('Comments')