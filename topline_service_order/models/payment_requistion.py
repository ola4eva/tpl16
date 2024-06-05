# -*- coding: utf-8 -*-

from odoo import models, fields, api


class topline_service_order_requisition(models.Model):
    _inherit = 'payment.requisition.form'

    service_order_id = fields.Many2one('service.order', 'Service Order')
    
