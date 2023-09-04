# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_account_id = fields.Many2one('account.account', string="Invoice Discount Account")
    bill_account_id = fields.Many2one('account.account', string="Bill Discount Account")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_global_discount = fields.Boolean(string="Global Discount For Invoice/Bill")
    invoice_account_id = fields.Many2one('account.account', string="Invoice Account",
                                         related='company_id.invoice_account_id')
    bill_account_id = fields.Many2one('account.account', string="Bill Account", related='company_id.bill_account_id')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            is_global_discount=(
                self.env['ir.config_parameter'].sudo().get_param('account_invoice_discount_app.is_global_discount')),
            # invoice_account_id=(self.env['ir.config_parameter'].sudo().get_param('account_invoice_discount_app.invoice_account_id.ids')),
            # bill_account_id=(
            #     self.env['ir.config_parameter'].sudo().get_param('account_invoice_discount_app.bill_account_id.ids')),

        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('account_invoice_discount_app.is_global_discount',
                                                         self.is_global_discount),
        # self.env['ir.config_parameter'].sudo().set_param('account_invoice_discount_app.invoice_account_id', self.invoice_account_id.id),
        # self.env['ir.config_parameter'].sudo().set_param('account_invoice_discount_app.bill_account_id',
        #                                                  self.bill_account_id.id)
