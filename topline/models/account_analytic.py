from odoo import models, fields


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    start_time = fields.Float(string='Start Time', required=True)
    start_time_am_pm = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')], string='AM/PM', copy=False)

    end_time = fields.Float(string='End Time', required=True)
    end_time_am_pm = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')], string='AM/PM', copy=False)
