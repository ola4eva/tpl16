# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models, _


class ExitForm(models.Model):
    _name = 'exit.form'
    _description = 'Exit Form (Working Hours)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.name

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('supervisor', 'Line Manager'),
        ('manager', 'HR Manager'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Applicants’s Name', required=True, default=_default_employee)
    job_id = fields.Many2one('hr.job', string='Function',
                             related="employee_id.job_id")
    applicant_function = fields.Char(
        string='Department', required=True, readonly=True, default=_default_department)
    purpose_of_exit = fields.Char(string='Purpose of Exit', required=True)
    time_of_leaving = fields.Datetime(string='Time of Leaving', required=True)
    time_of_returrning = fields.Datetime(
        string='Time of Returning', required=True)
    date = fields.Date(string="Date")
    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, tracking=True)
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)
    hr_approval = fields.Many2one(
        'res.users', 'HR Name', readonly=True, tracking=True)
    hr_approval_date = fields.Date(
        string='HR Date', readonly=True, tracking=True)

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'exit.form') or '/'
        return super(ExitForm, self).create(vals_list)

    def button_submit(self):
        self.write({'state': 'supervisor'})
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Exit Form '{}' for '{}' needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    def action_line_manager_approval(self):
        self.write({'state': 'manager'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        group_id = self.env.ref(
            'hr.group_hr_manager')
        subject = "Exit Form '{}' for '{}' has been approved by Line Manager".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_hr_approval(self):
        self.write({'state': 'approve'})
        self.hr_approval_date = date.today()
        self.hr_approval = self._uid
        subject = "Exit Form '{}' for '{}' has been approved by HR".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Exit Form '{}' for '{}' has been Rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
