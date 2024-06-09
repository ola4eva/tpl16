# -*- coding: utf-8 -*-

from datetime import date
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'create_date DESC'

    def _default_employee(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])

    state = fields.Selection(selection_add=[
        ('submit', 'Submitted'),
        ('approve', 'Line Manager Approved'),
        ('qa_qc_approve', 'QA/QC Approved'),
        ('waiting',),
        ('reject', 'Rejected'),
        ('cancel',)
    ])

    employee_id = fields.Many2one('hr.employee', 'Requesting Employee',
                                  states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=_default_employee,
                                  help="Default Owner")
    request_date = fields.Date(string='Date', default=date.today())
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', related='employee_id.department_id')
    project_id = fields.Many2one(
        'project.project', string='Project', index=True, ondelete='cascade', required=False)
    project_description = fields.Char('Project Description', copy=False)
