# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PettyCash(models.Model):
    _name = 'petty.cash'
    _description = 'Petty Cash'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('line_approve', 'Line Manager Approved'),
        ('internal_approve', 'Internal Audit Approved'),
        ('md_approve', 'MD Approved'),
        ('paid', 'Paid'),
        ('approve', 'Finance Approved'),
        ('post', 'Posted'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_payee(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)])
        return self.env['res.partner'].search([('name', '=', employee.name)])

    # 
    # def _check_manager_approval(self):
    #     current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id
    #     if self.employee_id.user_id == self.env.user:
    #         raise UserError(_("You cannot approve your own Request"))

    #     if not self.env.user in current_managers:
    #         raise UserError(_("You can only approve your department expenses"))

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'payment.requisition') or '/'
        return super(PettyCash, self).create(vals)

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    line_ids = fields.One2many(
        'petty.cash.line', 'petty_cash_id', string="Petty Cash form lines", copy=True)

    date = fields.Date(string='Date', required=True,
                       tracking=True)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', default=_default_department)
    project_description = fields.Char(
        string='Project Description',  tracking=True)
    payee_id = fields.Many2one(comodel_name='res.partner', required=False,
                               string='Name of Payee', default=_default_payee, tracking=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', required=True,
                                  string='Requesting Employee', default=_default_employee, tracking=True)
    currency_id = fields.Many2one(comodel_name='res.currency', required=True,
                                  string='Currency', default=_default_currency, tracking=True)
    bank_details = fields.Char(
        string='Bank Details',  tracking=True)

    total_amount_requested = fields.Float(
        string='Total amount requested', 
        compute='_total_amount_requested',
        store=True,
        readonly=True, 
        tracking=True)
    total_amount_approved = fields.Float(
        string='Total amount approved', compute='_total_amount_approved', readonly=True, tracking=True)
    discount = fields.Float('Discount (%)')

    total_amount_approved_due = fields.Float(
        string='Total amount Due', compute='_total_amount_approved', readonly=True)

    num_word = fields.Char(string="Amount Approved In Words:",
                           compute='_compute_amount_in_word')

    employee_name = fields.Many2one(
        'res.users', 'Employee Name', readonly=True, tracking=True)
    employee_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, tracking=True)
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    audit_approval = fields.Many2one(
        'res.users', 'Auditors Name', readonly=True, tracking=True)
    audit_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    md_approval = fields.Many2one(
        'res.users', 'Managing Director', readonly=True, tracking=True)
    md_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    finance_comments = fields.Char(
        string='Comments', tracking=True)
    finance_approval = fields.Many2one(
        'res.users', 'Finance Name', readonly=True, tracking=True)
    finance_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    received_approval = fields.Many2one(
        'res.users', 'Recipients Name',  tracking=True)
    received_approval_date = fields.Date(
        string='Date', tracking=True)

    journal_id = fields.Many2one('account.journal', string='Payment Journal', states={'done': [(
        'readonly', True)], 'post': [('readonly', True)]}, help="The journal used when the expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', states={'done': [('readonly', True)], 'post': [
                                      ('readonly', True)]}, help="The payment method used when the expense is paid by the company.")
    accounting_date = fields.Date("Date")
    account_move_id = fields.Many2one(
        'account.move', string='Journal Entry', ondelete='restrict', copy=False)

    source = fields.Char(string='Source')

    @api.constrains('total_amount_requested')
    def _constrains_total_amount_requested(self):
        if self.total_amount_requested > 10000:
            raise UserError("Please the limit for the petty cash is 10,000!!!")

    
    def button_submit(self):
        self.write({'state': 'submit'})
        self.employee_approval_date = date.today()
        self.employee_name = self._uid
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Petty Cash '{}', for {} needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    
    def button_line_manager_approval(self):
        # self._check_manager_approval()
        if self.total_amount_approved == 0.00:
            for line in self.line_ids:
                line.amount_approved = line.amount_requested
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
        subject = "Petty Cash '{}', for {} has been approved by supervisor".format(
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
        subject = "Petty Cash '{}', for '{}' needs approval".format(
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
        subject = "Petty Cash '{}', for '{}' has been approved by MD and needs approval from Finance".format(
            self.name,  self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    
    def button_finance_approval(self):
        self.write({'state': 'approve'})
        self.finance_approval_date = date.today()
        self.finance_approval = self._uid
        subject = "Petty Cash '{}', for {} has been approved by Finance".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    
    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Petty Cash '{}', for {} has been rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    
    @api.depends('line_ids.amount_requested')
    def _total_amount_requested(self):
        for line in self.line_ids:
            self.total_amount_requested += line.amount_requested

    
    @api.depends('line_ids.amount_approved')
    def _total_amount_approved(self):
        for line in self.line_ids:
            self.total_amount_approved += line.amount_approved
            self.total_amount_approved_due = self.total_amount_approved

    
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(
                rec.total_amount_approved)) + ' only'

    
    def action_sheet_move_create(self):

        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(
                _("You can only generate accounting entry for approved payment(s)."))

        if self.account_move_id:
            raise UserError(_("This Payment already has a journal entry ."))

        for requistion in self:
            account_move_obj = self.env['account.move'].sudo()
            move_vals = {
                'ref': requistion.name,
                'date': date.today(),
                'journal_id': requistion.bank_journal_id.id,
                'line_ids': [(0, 0, {
                             'name': requistion.payee_id.name,
                             'debit': line.amount_approved > 0 and line.amount_approved,
                             'credit': 0.0,
                             'account_id': line.account_id.id,
                             'analytic_account_id': line.analytic_account_id.id,
                             'date_maturity': date.today(),
                             'partner_id': requistion.payee_id.id,
                             }) for line in requistion.line_ids] +

                [(0, 0, {
                    'name': requistion.payee_id.name,
                    'credit': requistion.total_amount_approved > 0 and requistion.total_amount_approved,
                    'debit': 0.0,
                    'account_id': requistion.bank_journal_id.default_credit_account_id.id,
                    'date_maturity': date.today(),
                    'partner_id': requistion.payee_id.id,
                })]

            }
            account_move = account_move_obj.create(move_vals)
            requistion.account_move_id = account_move.id
        return True


class PettyCashLine(models.Model):
    _name = 'petty.cash.line'

    petty_cash_id = fields.Many2one(
        comodel_name='petty.cash', string='Petty Cash')

    
    def _check_user_group(self):
        if self.user_has_groups('account.group_account_manager') or self.user_has_groups('topline.group_hr_line_manager') or self.user_has_groups('topline.group_internal_audit'):
            self.is_manager = True

    is_manager = fields.Boolean(compute='_check_user_group')
    state = fields.Selection(
        related='petty_cash_id.state', store=True)
    name = fields.Char(string='Details/Purpose of Request', required=True)
    amount_requested = fields.Float(
        string='Amount Requested', required=True, tracking=True)
    amount_approved = fields.Float(
        string='Amount Approved', copy=False, tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', states={
                                          'post': [('readonly', True)], 'done': [('readonly', True)]}, oldname='analytic_account')
    account_id = fields.Many2one('account.account', string='Account', states={'post': [(
        'readonly', True)], 'done': [('readonly', True)]}, help="An Payment account is expected")
    
