# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrossoveredBudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'
    
    analytic_account_id = fields.Many2one('account.analytic.account', required=True)
    variance_amount = fields.Monetary(
        'Variance Amount', compute="_compute_budget_variance")
    
    def _compute_budget_variance(self):
        """Set variance amount to difference of planned amount and practical amount
        """
        for line in self:
            difference = 0
            if line.practical_amount and line.planned_amount:
                difference = line.planned_amount - line.practical_amount
            line.variance_amount = difference