# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit = 'fleet.vehicle'

    def _default_department(
            self):  # this method is to search the hr.employee and return the department id of the person clicking the form atm
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    def _default_employee(
            self):  # this method is to search the hr.employee and return the user id of the person clicking the form atm
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee Name:', default=_default_employee)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', default=_default_department)
    acquisition_date = fields.Date('Registration Date', required=False,
                                   default=fields.Date.today, help='Date when the vehicle has been Registered')
    asset_number = fields.Char(string='Asset Number')
    project_id = fields.Many2one(
        comodel_name='project.project', string='Project')
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    duration = fields.Char(string='Duration')
