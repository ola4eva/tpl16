# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from datetime import date

from odoo.exceptions import UserError


class CashAdvanceRequestForm(models.Model):
    _name = 'cash.advance.request.form'
    _description = 'Cash Advance Request Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('line_approve', 'Line Manager Approved'),
        ('internal_approve', 'Internal Audit Approved'),
        ('md_approve', 'MD Approved'),
        ('approve', 'Finance Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True,)

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cash.advance.request') or '/'
        return super(CashAdvanceRequestForm, self).create(vals)

    def _check_manager_approval(self):
        # if not self.user_has_groups('hr_expense.group_hr_expense_user'):
        #    raise UserError(_("Only Managers and HR Officers can approve expenses"))
        # elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
        current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id
        if self.employee_id.user_id == self.env.user:
            raise UserError(_("You cannot approve your own Request"))

        if not self.env.user in current_managers:
            raise UserError(_("You can only approve your department expenses"))

    cash_advance_request_form_line_ids = fields.One2many(
        'cash.advance.request.form.lines', 'cash_advance_request_form_id', string="cash advance request form lines", copy=True)

    date = fields.Date(string='Date', required=True,
                       tracking=True, default=date.today())
    employee_id = fields.Many2one(comodel_name='hr.employee', required=True,
                                  string='Name', tracking=True, default=_default_employee)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    related='employee_id.department_id', tracking=True,)
    location = fields.Char(string='Location', required=True,
                           tracking=True,)
    bank_details = fields.Char(
        string='Bank Details',  tracking=True,)

    currency_id = fields.Many2one(comodel_name='res.currency', required=True,
                                  string='Currency', default=_default_currency, tracking=True,)

    num_word = fields.Char(string="Amount In Words:",
                           compute='_compute_amount_in_word')

    total_amount = fields.Float(
        string='Total amount', compute='_total_amount', readonly=True)

    date_recovery = fields.Date(
        string='Date of Recovery', required=True, tracking=True,)

    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(
                rec.total_amount)) + ' only'

    @api.depends('cash_advance_request_form_line_ids.amount')
    def _total_amount(self):
        for line in self.cash_advance_request_form_line_ids:
            self.total_amount += line.amount

    employee_name = fields.Many2one(
        'res.users', 'Employee Name', readonly=True, tracking=True,),
    employee_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True,)

    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, tracking=True,)
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True,)

    audit_approval = fields.Many2one(
        'res.users', 'Auditors Name', readonly=True, tracking=True,)
    audit_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True,)

    finance_comments = fields.Char(
        string='Comments', tracking=True,)
    finance_approval = fields.Many2one(
        'res.users', 'Finance Name', readonly=True, tracking=True,)
    finance_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True,)

    received_approval = fields.Many2one(
        'res.users', 'Recipients Name',  tracking=True,)
    received_approval_date = fields.Date(
        string='Date', tracking=True,)
    paid = fields.Boolean(string="Paid")
    move_id = fields.Many2one(
        comodel_name="account.move", string="Accounting Entry")
    journal_id = fields.Many2one(
        comodel_name="account.journal", string="Journal")

    def button_submit(self):
        self.write({'state': 'submit'})
        self.employee_approval_date = date.today()
        self.employee_name = self._uid
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Cash Advance Request '{}', for {} needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    def button_line_manager_approval(self):
        self._check_manager_approval()
        self.write({'state': 'line_approve'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_internal_audit')
        partner_ids = []
        user_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Cash Advance Request '{}', for {} has been approved by supervisor".format(
            self.name, self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_audit_approval_notification(self):
        self.write({'state': 'internal_approve'})
        self.audit_approval_date = date.today()
        self.audit_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_md')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Cash Advance Request '{}', for '{}' needs approval from Audit".format(
            self.name, self.employee_id.name)
        # for partner in self.message_partner_ids:
        #   partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_md_approval_notification(self):
        self.write({'state': 'md_approve'})
        self.md_approval_date = date.today()
        self.md_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_finance_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Cash Advance Request '{}', for '{}' has been approved by MD and needs approval from Finance".format(
            self.name, self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_finance_approval(self):
        self.write({'state': 'approve'})
        self.finance_approval_date = date.today()
        self.finance_approval = self._uid
        subject = "Cash Advance Request '{}', for {} has been approved by Finance".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Cash Advance Request '{}', for {} has been rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def post_entries(self):
        requesting_partner = self.employee_id.user_id.partner_id
        move_vals = {
            'ref': self.name,
            'date': date.today(),
            'journal_id': self.journal_id.id,
            'line_ids': [(0, 0, {
                'name': self.name,
                'debit': self.total_amount > 0 and self.total_amount,
                'credit': 0.0,
                # Debit employee receivable
                'account_id': requesting_partner.property_account_receivable_id.id,
                'date_maturity': date.today(),
                'partner_id': requesting_partner.id,
            }),
                (0, 0, {
                    'name': self.name,
                    'credit': self.total_amount > 0 and self.total_amount,
                    'debit': 0.0,
                    'account_id': self.journal_id.default_credit_account_id.id,
                    'date_maturity': date.today(),
                    'partner_id': requesting_partner.id,
                })
            ]
        }
        account_move = self.env['account.move'].sudo().create(move_vals)
        self.move_id = account_move.id
        self.paid = True
        return True

    def reset_paid(self):
        self.paid = False
        return True


class CashAdvanceRequestFormLines(models.Model):
    _name = 'cash.advance.request.form.lines'

    cash_advance_request_form_id = fields.Many2one(
        comodel_name='cash.advance.request.form', string='cash advance request Form')

    name = fields.Char(string='DETAILS/PURPOSE OF REQUEST', required=True)
    account_id = fields.Many2one(
        comodel_name="account.account", string='Account')
    note = fields.Char(string='Description')
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account", string='Analytic Account')
    amount = fields.Float(string='AMOUNT', required=True)
