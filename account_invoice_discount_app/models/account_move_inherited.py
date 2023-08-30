# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    discount_type = fields.Selection([
        ('fix', 'Fixed'),
        ('percent', 'Percentage'),
    ], default='percent', help="Select the discount type.")

    discount = fields.Float(string="Discount")
    total_discount = fields.Float(string="Total Discount", compute="compute_total_discount", store=True)
    is_global_discount = fields.Boolean(String="Global Discount For Invoice/Bill",
                                        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
                                            'account_invoice_discount_app.is_global_discount'))

    @api.depends('invoice_line_ids', 'discount', 'discount_type')
    def compute_total_discount(self):
        print('jkk')
        for rec in self:
            total_discount = 0
            for line_id in rec.invoice_line_ids:
                if line_id.discount_type == 'percent':
                    if line_id.discount > 0:
                        # total_discount += (line_id.quantity * line_id.price_unit / line_id.discount)
                        total_discount += line_id.quantity * line_id.price_unit / line_id.discount
                elif line_id.discount_type == 'fix':
                    total_discount += line_id.discount
                else:
                    total_discount += 0
            if rec.discount_type == 'percent':
                if rec.discount > 0:
                    total_discount += (rec.amount_untaxed * rec.discount / 100)
            elif rec.discount_type == 'fix':
                total_discount += rec.discount
            else:
                total_discount += 0
            rec.total_discount = total_discount

    
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'discount', 'discount_type',
                 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'date')
    def _compute_amount(self):


        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)

        discount = 0
        if self.discount_type == 'percent':
            if self.discount > 0:
                discount = self.amount_untaxed * self.discount / 100

        elif self.discount_type == 'fix':
            discount = self.discount

        else:
            discount = 0

        self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)

        self.amount_total = self.amount_untaxed + self.amount_tax - discount
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id
            rate_date = self._get_currency_rate_date() or fields.Date.today()
            amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id,
                                                               self.company_id, rate_date)
            amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id,
                                                         self.company_id, rate_date)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual', 'discount', 'discount_type',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self._get_aml_for_amount_residual():
            residual_company_signed += line.amount_residual
            if line.currency_id == self.currency_id:
                residual += line.amount_residual_currency if line.currency_id else line.amount_residual
            else:
                if line.currency_id:
                    residual += line.currency_id._convert(line.amount_residual_currency, self.currency_id,
                                                          line.company_id, line.date or fields.Date.today())
                else:
                    residual += line.company_id.currency_id._convert(line.amount_residual, self.currency_id,
                                                                     line.company_id, line.date or fields.Date.today())

        if self.type in ('', 'in_refund', 'out_invoice'):
            if self.discount_type == 'percent':
                if self.discount > 0:
                    residual -= (self.amount_untaxed * self.discount / 100)
                    residual_company_signed -= (self.amount_untaxed * self.discount / 100)

            elif self.discount_type == 'fix':
                residual -= self.discount
                residual_company_signed -= self.discount

            else:
                residual += 0
                residual_company_signed += 0

        else:
            if self.discount_type == 'percent':
                if self.discount > 0:
                    residual += (self.amount_untaxed * self.discount / 100)
                    residual_company_signed += (self.amount_untaxed * self.discount / 100)

            elif self.discount_type == 'fix':
                residual += self.discount
                residual_company_signed += self.discount

            else:
                residual += 0
                residual_company_signed += 0

        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    _description = "Invoice Line"

    discount_type = fields.Selection([
        ('fix', 'Fixed'),
        ('percent', 'Percentage'),
    ], default='percent', help="Select the discount type.")

    
    @api.depends('price_unit', 'discount', 'discount_type', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        # price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        discount = 0
        if self.discount_type == 'percent':
            if self.discount > 0:
                price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            else:
                price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

        elif self.discount_type == 'fix':
            if self.discount > 0:
                price = self.price_unit - (self.discount / self.quantity)
            else:
                price = self.price_unit

        else:
            price = self.price_unit

        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else (self.quantity * price)
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(price_subtotal_signed, self.invoice_id.company_id.currency_id,
                                                      self.company_id or self.env.user.company_id,
                                                      date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
