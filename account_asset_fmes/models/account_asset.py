# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    already_depreciated_amount_import_custom = fields.Monetary(
        'Depreciated Amount (Custom)', readonly=True, states={'draft': [('readonly', False)]})
    original_value_custom = fields.Monetary(
        'Original Value (Custom)', readonly=True, states={'draft': [('readonly', False)]})
