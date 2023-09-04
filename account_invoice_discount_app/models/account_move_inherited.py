# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    discount_type = fields.Selection([
        ('fix', 'Fixed'),
        ('percent', 'Percentage'),
    ], default='percent', help="Select the discount type.")

    discount = fields.Float(string="Discount")
    total_discount = fields.Float(string="Total Discount", compute="compute_total_discount", store=True)
    is_global_discount = fields.Boolean(string="Global Discount For Invoice/Bill",
                                        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
                                            'account_invoice_discount_app.is_global_discount'))

    @api.depends('invoice_line_ids', 'discount', 'discount_type')
    def compute_total_discount(self):
        for rec in self:
            total_discount = 0
            for line_id in rec.invoice_line_ids:
                if line_id.discount_type == 'percent':
                    if line_id.discount > 0:
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
            self.total_discount = total_discount
            # if self.discount > 0:
            #     for line_id in self.line_ids:
            #         if line_id.account_id == rec.partner_id.property_account_receivable_id:
            #             line_id.with_context(check_move_validity=False).debit = rec.amount_total
            #             # line_id.debit -= line_id.discount
            #             print(line_id.debit,'jjjjjjjjjjjjjjjjj')
            #     amount = rec.discount
            #     account_id = self.env['ir.config_parameter'].sudo().get_param('account_invoice_discount_app.invoice_account_id.id')
            #     print(account_id,'account_id')
            #     man_id_cr=self.env['account.move.line'].create({
            #         'name': 'Global Discount Of:' + rec.partner_id.name,
            #         'account_id':2,
            #         'journal_id': rec.journal_id.id,
            #         'date': rec.invoice_date,
            #         'debit': 0.0,
            #         'credit': rec.discount,
            #         'move_id': 1,
            #     })
            # line_ids.append(credit_line)

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'discount_type',
        'discount',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:
            total_untaxed, total_untaxed_currency = 0.0, 0.0
            total_tax, total_tax_currency = 0.0, 0.0
            total_residual, total_residual_currency = 0.0, 0.0
            total, total_currency = 0.0, 0.0

            for line in move.line_ids:
                if move.is_invoice(True):
                    # === Invoices ===
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type == 'payment_term':
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency

                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency
            if move.move_type in ('', 'in_refund', 'out_invoice'):
                if move.discount_type == 'percent':
                    if move.discount > 0:
                        total += (total_untaxed * move.discount / 100)
                        total_currency += (total_untaxed * move.discount / 100)
                        total_residual -= (total_untaxed * move.discount / 100)
                        total_residual_currency -= (total_untaxed * move.discount / 100)
                elif move.discount_type == 'fix':
                    total += move.discount
                    total_currency += move.discount
                    total_residual -= move.discount
                    total_residual_currency -= move.discount
                else:
                    total += 0
                    total_currency += 0
                    total_residual += 0
                    total_residual_currency += 0
            else:
                if move.discount_type == 'percent':
                    if move.discount > 0:
                        total -= (total_untaxed * move.discount / 100)
                        total_currency -= (total_untaxed * move.discount / 100)
                        total_residual += (total_untaxed * move.discount / 100)
                        total_residual_currency += (total_untaxed * move.discount / 100)
                elif move.discount_type == 'fix':
                    total -= move.discount
                    total_currency -= move.discount
                    total_residual += move.discount
                    total_residual_currency += move.discount
                else:
                    total += 0
                    total_currency += 0
                    total_residual += 0
                    total_residual_currency += 0

            sign = move.direction_sign
            move.amount_untaxed = sign * total_untaxed_currency
            move.amount_tax = sign * total_tax_currency
            move.amount_total = sign * total_currency
            move.amount_residual = -sign * total_residual_currency
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(
                        sign * move.amount_total)

    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
        'discount_type',
        'discount',
    )
    def _compute_tax_totals(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        for move in self:
            if move.is_invoice(include_receipts=True):
                base_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
                base_line_values_list = [line._convert_to_tax_base_line_dict() for line in base_lines]

                if move.id:
                    # The invoice is stored so we can add the early payment discount lines directly to reduce the
                    # tax amount without touching the untaxed amount.
                    sign = -1 if move.is_inbound(include_receipts=True) else 1
                    base_line_values_list += [
                        {
                            **line._convert_to_tax_base_line_dict(),
                            'handle_price_include': False,
                            'quantity': 1.0,
                            'price_unit': sign * line.amount_currency,
                        }
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'epd')
                    ]

                kwargs = {
                    'base_lines': base_line_values_list,
                    'currency': move.currency_id,
                }

                if move.id:
                    kwargs['tax_lines'] = [
                        line._convert_to_tax_line_dict()
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'tax')
                    ]
                else:
                    # In case the invoice isn't yet stored, the early payment discount lines are not there. Then,
                    # we need to simulate them.
                    epd_aggregated_values = {}
                    for base_line in base_lines:
                        if not base_line.epd_needed:
                            continue
                        for grouping_dict, values in base_line.epd_needed.items():
                            epd_values = epd_aggregated_values.setdefault(grouping_dict, {'price_subtotal': 0.0})
                            epd_values['price_subtotal'] += values['price_subtotal']

                    for grouping_dict, values in epd_aggregated_values.items():
                        taxes = None
                        if grouping_dict.get('tax_ids'):
                            taxes = self.env['account.tax'].browse(grouping_dict['tax_ids'][0][2])

                        kwargs['base_lines'].append(self.env['account.tax']._convert_to_tax_base_line_dict(
                            None,
                            partner=move.partner_id,
                            currency=move.currency_id,
                            taxes=taxes,
                            price_unit=values['price_subtotal'],
                            quantity=1.0,
                            account=self.env['account.account'].browse(grouping_dict['account_id']),
                            analytic_distribution=values.get('analytic_distribution'),
                            price_subtotal=values['price_subtotal'],
                            is_refund=move.move_type in ('out_refund', 'in_refund'),
                            handle_price_include=False,
                        ))
                print(kwargs,':kwargs')
                move.tax_totals = self.env['account.tax']._prepare_tax_totals(**kwargs)
                total = 0
                if move.move_type in ('', 'in_refund', 'out_invoice'):
                    if move.discount_type == 'percent':
                        if move.discount > 0:
                            total -= (move.amount_untaxed * move.discount / 100)
                    elif move.discount_type == 'fix':
                        total -= move.discount
                    else:
                        total += 0
                else:
                    if move.discount_type == 'percent':
                        if move.discount > 0:
                            total += (move.amount_untaxed * move.discount / 100)
                    elif move.discount_type == 'fix':
                        total += move.discount
                    else:
                        total += 0
                print(move.tax_totals)
                move.tax_totals['formatted_amount_total'] = move.currency_id.symbol + ' ' + str(move.amount_total)
                move.tax_totals['amount_total'] = move.amount_total

            else:
                # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
                move.tax_totals = None


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"
    _description = "Invoice Line"

    discount_type = fields.Selection([
        ('fix', 'Fixed'),
        ('percent', 'Percentage'),
    ], default='percent', help="Select the discount type.")

    @api.depends('quantity', 'discount','discount_type' ,'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        for line in self:
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = False
            # Compute 'price_subtotal'.
            # line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))

            if line.discount_type == 'percent':
                line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            elif line.discount_type == 'fix':
                line_discount_price_unit = line.price_unit - (line.discount / line.quantity)
            else:
                line_discount_price_unit = line.price_unit

            subtotal = line.quantity * line_discount_price_unit

            # Compute 'price_total'.
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
            else:
                line.price_total = line.price_subtotal = subtotal


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"


    def _get_total_amount_in_wizard_currency_to_full_reconcile(self, batch_result, early_payment_discount=True):
        """ Compute the total amount needed in the currency of the wizard to fully reconcile the batch of journal
        items passed as parameter.

        :param batch_result:    A batch returned by '_get_batches'.
        :return:                An amount in the currency of the wizard.
        """
        self.ensure_one()
        comp_curr = self.company_id.currency_id
        discount =0
        for line_id in self.line_ids:
            if line_id.move_id.move_type in ('', 'in_refund', 'out_invoice'):
                if line_id.move_id.discount_type == 'percent':
                    if line_id.move_id.discount > 0:
                        discount -= (line_id.move_id.amount_untaxed * line_id.move_id.discount / 100)
                elif line_id.move_id.discount_type == 'fix':
                    discount -= line_id.move_id.discount
                else:
                    discount += 0
            else:
                if line_id.move_id.discount_type == 'percent':
                    if line_id.move_id.discount > 0:
                        discount -= (line_id.move_id.amount_untaxed * line_id.move_id.discount / 100)
                elif line_id.move_id.discount_type == 'fix':
                    discount -= line_id.move_id.discount
                else:
                    discount += 0

        if self.source_currency_id == self.currency_id:
            # Same currency (manage the early payment discount).
            print("IF")
            return self._get_total_amount_using_same_currency(batch_result, early_payment_discount=early_payment_discount)
        elif self.source_currency_id != comp_curr and self.currency_id == comp_curr:
            # Foreign currency on source line but the company currency one on the opposite line.
            print("ELIF1")
            return self.source_currency_id._convert(
                self.source_amount_currency - discount,
                comp_curr,
                self.company_id,
                self.payment_date,
            ), False
        elif self.source_currency_id == comp_curr and self.currency_id != comp_curr:
            print("ELIF2")
            # Company currency on source line but a foreign currency one on the opposite line.
            return abs(sum(
                comp_curr._convert(
                    aml.amount_residual - discount,
                    self.currency_id,
                    self.company_id,
                    aml.date,
                )
                for aml in batch_result['lines']
            )), False
        else:
            print("ELSE")
            # Foreign currency on payment different than the one set on the journal entries.
            return comp_curr._convert(
                self.source_amount - discount,
                self.currency_id,
                self.company_id,
                self.payment_date,
            ), False

    def _get_total_amount_using_same_currency(self, batch_result, early_payment_discount=True):
        self.ensure_one()
        amount = 0.0
        mode = False

        discount = 0
        for line_id in self.line_ids:
            if line_id.move_id.move_type in ('', 'in_refund', 'out_invoice'):
                if line_id.move_id.discount_type == 'percent':
                    if line_id.move_id.discount > 0:
                        discount += (line_id.move_id.amount_untaxed * line_id.move_id.discount / 100)
                elif line_id.move_id.discount_type == 'fix':
                    discount += line_id.move_id.discount
                else:
                    discount += 0
            else:
                if line_id.move_id.discount_type == 'percent':
                    if line_id.move_id.discount > 0:
                        discount -= (line_id.move_id.amount_untaxed * line_id.move_id.discount / 100)
                elif line_id.move_id.discount_type == 'fix':
                    discount -= line_id.move_id.discount
                else:
                    discount += 0

        for aml in batch_result['lines']:
            if early_payment_discount and aml._is_eligible_for_early_payment_discount(aml.currency_id, self.payment_date):
                amount += aml.discount_amount_currency - discount
                mode = 'early_payment'
            else:
                amount += aml.amount_residual_currency - discount
        return abs(amount), mode

    @api.model
    def _get_wizard_values_from_batch(self, batch_result):
        print("MY OVERRIDE")
        ''' Extract values from the batch passed as parameter (see '_get_batches')
        to be mounted in the wizard view.
        :param batch_result:    A batch returned by '_get_batches'.
        :return:                A dictionary containing valid fields
        '''
        payment_values = batch_result['payment_values']
        lines = batch_result['lines']
        company = lines[0].company_id

        source_amount = abs(sum(lines.mapped('amount_residual')))
        if payment_values['currency_id'] == company.currency_id.id:
            source_amount_currency = source_amount
        else:
            source_amount_currency = abs(sum(lines.mapped('amount_residual_currency')))

        for line_id in self.line_ids:
            if line_id.move_id.move_type in ('', 'in_refund', 'out_invoice'):
                if line_id.move_id.discount_type == 'percent':
                    if line_id.move_id.discount > 0:
                        source_amount -= (line_id.move_id.amount_untaxed * line_id.move_id.discount / 100)
                        source_amount_currency -= (line_id.move_id.amount_untaxed * line_id.move_id.discount / 100)
                elif line_id.move_id.discount_type == 'fix':
                    source_amount -= line_id.move_id.discount
                    source_amount_currency -= line_id.move_id.discount
                else:
                    source_amount += 0
                    source_amount_currency += 0
            else:
                if line_id.move_id.discount_type == 'percent':
                    if line_id.move_id.discount > 0:
                        source_amount -= (line_id.move_id.amount_untaxed * line_id.move_id.discount / 100)
                        source_amount_currency -= (line_id.move_id.amount_untaxed * line_id.move_id.discount / 100)
                elif line_id.move_id.discount_type == 'fix':
                    source_amount -= line_id.move_id.discount
                    source_amount_currency -= line_id.move_id.discount
                else:
                    source_amount += 0
                    source_amount_currency += 0

        return {
            'company_id': company.id,
            'partner_id': payment_values['partner_id'],
            'partner_type': payment_values['partner_type'],
            'payment_type': payment_values['payment_type'],
            'source_currency_id': payment_values['currency_id'],
            'source_amount': source_amount,
            'source_amount_currency': source_amount_currency,
        }
