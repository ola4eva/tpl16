# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError

YEAR_TUPLE = [
    ('2024', '2024'),
    ('2025', '2025'),
    ('2026', '2026'),
    ('2027', '2027'),
    ('2028', '2028'),
    ('2029', '2029'),
    ('2030', '2030'),
    ('2031', '2031'),
    ('2032', '2032'),
    ('2033', '2033'),
    ('2034', '2034'),
    ('2035', '2035'),
    ('2036', '2036'),
    ('2037', '2037'),
    ('2038', '2038'),
    ('2039', '2039'),
    ('2040', '2040'),
    ('2041', '2041'),
    ('2042', '2042'),
    ('2043', '2043'),
    ('2044', '2044'),
    ('2045', '2045'),
    ('2046', '2046'),
    ('2047', '2047'),
    ('2048', '2048'),
    ('2049', '2049'),
    ('2050', '2050'),
]


class SalaryAdvanceForm(models.Model):
    _name = 'salary.advance.form'
    _description = 'Salary Advance Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    def _check_manager_approval(self):
        # if not self.user_has_groups('hr_expense.group_hr_expense_user'):
        #    raise UserError(_("Only Managers and HR Officers can approve expenses"))
        # elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
        current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id
        if self.employee_id.user_id == self.env.user:
            raise UserError(_("You cannot approve your own Request"))

        if not self.env.user in current_managers:
            raise UserError(_("You can only approve your department expenses"))

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('line_approve', 'Line Manager Approved'),
        ('internal_approve', 'Internal Audit Approved'),
        ('md_approve', 'MD Approved'),
        ('approve', 'Finance Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    employee_id = fields.Many2one(comodel_name='hr.employee', required=True,
                                  string='Name', tracking=True, default=_default_employee)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    related='employee_id.department_id', tracking=True)
    job_title = fields.Char(
        string='Job Title', related='employee_id.job_title', tracking=True)

    advance_of = fields.Float(
        string='Advance of', required=True, tracking=True)
    month_of = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                                 ('5', 'May'), ('6', 'June'), ('7',
                                                               'July'), ('8', 'August'),
                                 ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                                string='Month of', required=True, tracking=True)
    pay_off_month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                                      ('5', 'May'), ('6', 'June'), ('7',
                                                                    'July'), ('8', 'August'),
                                      ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                                     string='Month', required=True, tracking=True)
    request_year = fields.Selection(
        selection=YEAR_TUPLE, string='Request Year')

    pay_off_year = fields.Selection(
        selection=YEAR_TUPLE, string='Pay Off Year')

    employee_name = fields.Many2one(
        'res.users', 'Employee Name', readonly=True, tracking=True)
    employee_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, tracking=True)
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    finance_comments = fields.Char(
        string='Comments', tracking=True)
    finance_approval = fields.Many2one(
        'res.users', 'Account Manager Name', readonly=True, tracking=True)
    finance_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'salary.advance') or '/'
        return super(SalaryAdvanceForm, self).create(vals_list)

    def button_submit(self):
        self.write({'state': 'submit'})
        self.employee_approval_date = date.today()
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Salary Advance '{}',  for {} needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    def button_line_manager_approval(self):
        self._check_manager_approval()
        self.write({'state': 'line_approve'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        group_id = self.env.ref(
            'topline.group_internal_audit')
        partner_ids = []
        user_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Salary Advance '{}', for {} has been approved by supervisor and needs approval from Audit".format(
            self.name, self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_audit_approval_notification(self):
        self.write({'state': 'internal_approve'})
        self.audit_approval_date = date.today()
        self.audit_approval = self._uid
        group_id = self.env.ref(
            'topline.group_md')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Salary Advance '{}', for '{}' needs approval from MD".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_md_approval_notification(self):
        self.write({'state': 'md_approve'})
        self.md_approval_date = date.today()
        self.md_approval = self._uid
        group_id = self.env.ref(
            'topline.group_finance_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Salary Advance '{}', for '{}' has been approved by MD and needs approval from Finance".format(
            self.name,  self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_finance_approval(self):
        self.write({'state': 'approve'})
        self.finance_approval_date = date.today()
        self.finance_approval = self._uid
        subject = "Salary Advance '{}', for {} has been approved by Finance".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Salary Advance '{}' for {} has been rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        
    @api.constrains('request_year', 'pay_off_year')
    def _check_request_recovery_year(self):
        """Check that the pay back year is greater than or equal to request year"""
        for record in self:
            if self.request_year and self.pay_off_year:
                if int(record.pay_off_year) < int(record.request_year):
                    raise UserError("Pay back year is ahead of request year") 