# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    active = fields.Boolean('Active', default=True)
    department_id = fields.Many2one(comodel_name='hr.department', string="Department")

    def get_total(self, code):
        return self.env['hr.payslip.line'].search([('slip_id', '=', self.id), ('code', '=', code)], limit=1).total
    
    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'employee_id' in values:
                employee = self.env['hr.employee'].sudo().search([('id', '=', values['employee_id'])], limit=1)
                values['department_id'] = employee.department_id.id
        return super(HRPayslip, self).create(vals_list)

    
    def unlink(self):
        for payslip in self:
            if not payslip.state == 'draft':
                raise UserError(
                    _("For a payslip to be deleted, it must first be set to draft"))
        return super(HRPayslip, self).unlink()
