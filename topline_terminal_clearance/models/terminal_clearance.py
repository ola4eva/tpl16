# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TerminalClearance(models.Model):
    _name = 'terminal.clearance'
    _rec_name = 'employee_id'
    _description = 'Terminal Clearance Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_department(
            self):  # this method is to search the hr.employee and return the user id of the person clicking the form atm
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

    terminal_clearance_line_ids = fields.One2many(comodel_name="terminal.clearance.returns.lines", inverse_name="terminal_clearance_id",
                                                  string="ITEMS RETURNED", required=False, )

    state = fields.Selection(string="Status", selection=[
        ('draft', 'Draft'), 
        ('confirm', 'Confirm'), 
        ('validate', 'Validate'),
        ('approved', 'Approved'),
        ('refuse', 'Refuse'), 
        ], default="draft", track_visibility='onchange')

    
    def confirm_request(self):
        self.state = 'confirm'

    
    def validate_request(self):
        self.state = 'validate'

    
    def refuse_request(self):
        self.state = 'refuse'

    
    def approve_request(self):
        self.state = 'approved'


class TerminalClearanceReturnLines(models.Model):
    _name = 'terminal.clearance.returns.lines'
    _description = 'Items Returned for Terminal Clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    items_id = fields.Many2one(
        comodel_name='product.template', string='ITEMS RETURNED')
    quantity = fields.Integer(string="Quantity", required=False, )
    terminal_clearance_id = fields.Many2one(
        comodel_name="terminal.clearance", string="Items", required=False, )
