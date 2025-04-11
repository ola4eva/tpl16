# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2024 HyperiT Consultant (www.hyperitconsultant.com>)
#
#    For Module Support : ola4eva2001@gmail.com  or Skype : lukmanyusuff
#
##############################################################################

from odoo import models, fields, api
from num2words import num2words


class account_move(models.Model):
    _inherit = 'account.move'
    
    num_word = fields.Char(string="Amount In Words:",compute='_compute_amount_in_word')
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(
                rec.amount_total)) + ' only '
