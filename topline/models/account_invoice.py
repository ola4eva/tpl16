# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from ast import literal_eval
from odoo.tools import float_compare


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(
                rec.amount_total)) + ' only'

    num_word = fields.Char(string="Amount In Words:",
                           compute='_compute_amount_in_word')

    partner_bank_ids = fields.Many2many('res.partner.bank', string='Bank Accounts',
                                        help='Bank Account Numbers to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Vendor Credit Note, otherwise a Partner bank account number.',
                                        readonly=True, states={'draft': [('readonly', False)]})  # Default value computed in default_get for out_invoices

    @api.model
    def default_get(self, default_fields):
        """ Compute default partner_bank_id field for 'out_invoice' type,
        using the default values computed for the other fields.
        """
        res = super(AccountInvoice, self).default_get(default_fields)

        if not res.get('type', False) == 'out_invoice' or not 'company_id' in res:
            return res

        company = self.env['res.company'].browse(res['company_id'])
        if company.partner_id:
            partner_bank_result = self.env['res.partner.bank'].search(
                [('partner_id', '=', company.partner_id.id)], limit=1)
            if partner_bank_result:
                res['partner_bank_id'] = partner_bank_result.id
                # for line in self.partner_bank_ids:
                res['partner_bank_ids'] = partner_bank_result.id
        return res



