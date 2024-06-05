# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    service_order_id = fields.Many2one('service.order', string='Service Order')