# -*- coding: utf-8 -*-

from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pprint
pp = pprint.PrettyPrinter(indent=4)


class PaymentRequisitionForm(models.Model):
    _name = 'payment.requisition.form'
    _description = 'PAYMENT REQUISITION FORM'
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

    def _check_manager_approval(self):
        current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id
        if self.employee_id.user_id == self.env.user:
            raise UserError(_("You cannot approve your own Request"))

        if not self.env.user in current_managers:
            raise UserError(_("You can only approve your department expenses"))

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    payment_requisition_form_line_ids = fields.One2many(
        'payment.requisition.form.lines', 'payment_requisition_form_id', string="payment requisition form lines", copy=True)

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

    bank_id = fields.Many2one('res.bank', string='Bank')
    account_number = fields.Char('Account No', size=10)

    total_amount_requested = fields.Float(
        string='Total amount requested', compute='_total_amount_requested', readonly=True, tracking=True,)
    total_amount_approved = fields.Float(
        string='Total amount approved', compute='_total_amount_approved', readonly=True, tracking=True,)
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

    service_order_id = fields.Many2one('service.order', 'Service Order')
    atp_id = fields.Many2one(comodel_name='atp.form', string='ATP Form')
    source = fields.Char(string='Source')

    md_request = fields.Boolean(string="MD's Request", copy=False)
    payment_ids = fields.One2many(
        'account.move', 'requisition_id', "Payments", copy=False)
    fully_paid = fields.Boolean("Fully paid", default=False, copy=False)
    default_expense_account_id = fields.Many2one(
        "account.account", string="Default Expense Account", copy=False, readonly=True, states={
            'approve': [('readonly', False)]})
    default_analytic_account_id = fields.Many2one('account.analytic.account', string='Default Analytic Account', readonly=True, states={
        'approve': [('readonly', False)]})
    payment_count = fields.Integer(
        "Total Payments", compute="_compute_total_payments")
    total_amount_paid = fields.Float(
        string='Total Amount Paid', default=0.0, readonly=True)
    total_amount_outstanding = fields.Float(
        string='Total Amount Outstanding', compute="_total_amount_outstanding")
    rejection_log_ids = fields.One2many(
        comodel_name='payment.requisition.rejection.log', inverse_name='requisition_id', string='Rejection Logs')

    def _total_amount_outstanding(self):
        self.total_amount_outstanding = self.total_amount_approved - self.total_amount_paid

    def _compute_amount_paid(self, amount_paid=0.0):
        self.total_amount_paid += amount_paid

    def _confirm_post(self):
        if all(state == 'posted' for state in self.payment_ids.mapped('state')):
            self.state = 'post'
        else:
            self.state = self.state

    def _compute_total_payments(self):
        self.payment_count = self.env['account.move'].sudo().search_count(
            [('requisition_id', '=', self.id)])

    def _check_fully_paid(self):
        payments = self.payment_ids.mapped('amount')
        payment_till_date = sum(payments)
        self.fully_paid = payment_till_date == self.total_amount_approved

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'payment.requisition') or '/'
        return super(PaymentRequisitionForm, self).create(vals_list)

    @api.model
    def create(self, values):
        if values.get("payee_id"):
            payee_id = values.get("payee_id")
            is_md = self.is_md(payee_id)
            if is_md is True:
                values['state'] = "md_approve"
            elif is_md is False and values.get('md_request') is True:
                values["state"] = "md_approve"
        res = super().create(values)
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _("You cannot delete a record that is not in draft"))

    def is_md(self, partner_id=None):
        if not partner_id:
            return False
        user = self.env['res.users'].search(
            [('partner_id', '=', int(partner_id))])
        if user:
            return user.has_group("topline.group_md")
        return False

    @api.onchange('default_expense_account_id')
    def _onchange_default_expense_account_id(self):
        for record in self:
            if record.default_expense_account_id:
                if record.payment_requisition_form_line_ids:
                    record.payment_requisition_form_line_ids.write({
                        'account_id': record.default_expense_account_id.id
                    })

    @api.onchange('default_analytic_account_id')
    def _onchange_default_analytic_account_id(self):
        for record in self:
            if record.default_analytic_account_id:
                if record.payment_requisition_form_line_ids:
                    record.payment_requisition_form_line_ids.write({
                        'analytic_account_id': record.default_analytic_account_id.id
                    })

    def button_submit(self):
        requester = self.env['res.users'].search(
            [('partner_id', '=', self.payee_id.id)])
        is_internal_auditor = requester.has_group(
            'topline.group_internal_audit')
        self.write(
            {'state': 'submit' if not is_internal_auditor else 'internal_approve'})
        self.employee_approval_date = date.today()
        self.employee_name = self._uid
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Payment Requisition '{}', for {} needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    def set_to_draft(self):
        return self.write({'state': 'draft'})

    def register_payment(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": 'payment_requisition.register_payment',
            "views": [[False, "form"]],
            "context": {'default_requisition_id': self.id, 'default_amount': self.total_amount_approved, 'default_total_amount_outstanding': self.total_amount_outstanding},
            "target": "new",
        }

    def action_sheet_move_create(self, payment_type, amount=None):

        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(
                _("You can only generate accounting entry for approved payment(s)."))

        if not self.bank_journal_id:
            raise UserError(
                _("No journal selected."))

        if any(list(not line.account_id for sheet in self for line in sheet.payment_requisition_form_line_ids)):
            if (not self.default_expense_account_id):
                raise UserError(
                    _("No default expense account selected and no expense account set on the lines."))
        if not amount:
            amount = 0.0
        for requisition in self:
            account_move_obj = self.env['account.move'].sudo()
            move_vals = {}
            if payment_type == 'full_payment':
                move_vals = {
                    'ref': requisition.name,
                    'date': date.today(),
                    'journal_id': requisition.bank_journal_id.id,
                    'line_ids': [(0, 0, {
                        'name': requisition.payee_id.name,
                        'debit': line.amount_approved > 0 and line.amount_approved,
                        'credit': 0.0,
                        'account_id': line.account_id.id or requisition.default_expense_account_id.id,
                        # 'analytic_account_id': line.analytic_account_id.id or requisition.default_analytic_account_id.id,
                        'date_maturity': date.today(),
                        'partner_id': requisition.payee_id.id,
                    }) for line in requisition.payment_requisition_form_line_ids] +

                    [(0, 0, {
                        'name': requisition.payee_id.name,
                        'credit': requisition.total_amount_approved > 0 and requisition.total_amount_approved,
                        'debit': 0.0,
                        'account_id': requisition.bank_journal_id.default_account_id.id,
                        'date_maturity': date.today(),
                        'partner_id': requisition.payee_id.id,
                    })]

                }
            else:
                move_vals = {
                    'ref': requisition.name,
                    'date': date.today(),
                    'journal_id': requisition.bank_journal_id.id,
                    'line_ids': [(0, 0, {
                        'name': requisition.payee_id.name,
                        'debit': amount > 0 and amount,
                        'credit': 0.0,
                        'account_id': requisition.default_expense_account_id.id,
                        # 'analytic_account_id': requisition.default_analytic_account_id.id,
                        'date_maturity': date.today(),
                        'partner_id': requisition.payee_id.id,
                    })] +

                    [(0, 0, {
                        'name': requisition.payee_id.name,
                        'credit': amount > 0 and amount,
                        'debit': 0.0,
                        'account_id': requisition.bank_journal_id.default_account_id.id,
                        'date_maturity': date.today(),
                        'partner_id': requisition.payee_id.id,
                    })]

                }
            pp.pprint(move_vals)
            account_move = account_move_obj.create(move_vals)
            requisition.account_move_id = account_move.id
            self._compute_amount_paid(amount)
            requisition.write({
                'payment_ids': [(4, account_move.id, 0)]
            })
            # TODO: revisit this function
            # requisition._check_fully_paid()
        return True

    def action_view_journal_entries(self):
        """
        This function returns an action that display existing journal entries of the give payment requisition.
        When only one found, show the journal entry immediately.
        Returns
        -------
        """
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        if len(self.payment_ids) != 1:
            result['domain'] = "[('id', 'in', " + \
                str(self.payment_ids.ids) + ")]"
        elif len(self.payment_ids) == 1:
            res = self.env.ref('account.view_move_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.payment_ids.id
        return result

    def action_finance_reject(self):
        """Open the wizard to input the rejection reason
        """
        return {
            "name": "Reject Reason",
            "type": "ir.actions.act_window",
            'views': [(False, 'form')],
            "res_model": "reject.payment.requisition",
            "view_form": "form",
            "target": "new",
            "context": {
                'default_requisition_id': self.id,
                'default_user_id': self.env.uid,
            }
        }

    def button_line_manager_approval(self):
        # self._check_manager_approval()
        if self.total_amount_approved == 0.00:
            for line in self.payment_requisition_form_line_ids:
                line.amount_approved = line.amount_requested
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
        subject = "Payment Requisition '{}', for {} has been approved by supervisor".format(
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
        subject = "Payment Requisition '{}', for '{}' needs approval".format(
            self.name, self.employee_id.name)
        # for partner in self.message_partner_ids:
        #   partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_md_approval_notification(self):
        user = self.env.user
        is_md = self.is_md(user.partner_id.id)
        if not is_md and user.has_group("payment_requisition.approve_payment_for_md"):
            allowed_limit = user.company_id.md_proxy_approval_limit
            if self.total_amount_approved > allowed_limit:
                raise UserError(
                    "This amount is above your allowed limit. You are allowed to approve amounts up to %s!" % str(allowed_limit))
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
        subject = "Payment Requisition '{}', for '{}' has been approved by MD and needs approval from Finance".format(
            self.name,  self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return True

    def button_finance_approval(self):
        for record in self:
            if any(line.amount_approved == False for line in record.payment_requisition_form_line_ids):
                raise UserError(
                    _("No approved amount on some lines."))
        self.write({'state': 'approve'})
        self.finance_approval_date = date.today()
        self.finance_approval = self._uid
        subject = "Payment Requisition '{}', for {} has been approved by Finance".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Payment Requisition '{}', for {} has been rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.depends('payment_requisition_form_line_ids.amount_requested')
    def _total_amount_requested(self):
        self.total_amount_requested = 0
        for line in self.payment_requisition_form_line_ids:
            self.total_amount_requested += line.amount_requested

    @api.depends('payment_requisition_form_line_ids.amount_approved')
    def _total_amount_approved(self):
        self.total_amount_approved = self.total_amount_approved_due = 0.0
        for line in self.payment_requisition_form_line_ids:
            self.total_amount_approved += line.amount_approved
            self.total_amount_approved_due = self.total_amount_approved

    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(
                rec.total_amount_approved)) + ' only'


class PaymentRequisitionFormLines(models.Model):
    _name = 'payment.requisition.form.lines'
    _description = 'Payment Requisition Form Lines'

    payment_requisition_form_id = fields.Many2one(
        comodel_name='payment.requisition.form', string='payment.requisition.form')

    def _check_user_group(self):
        is_manager = False
        if self.user_has_groups('account.group_account_manager') or self.user_has_groups('topline.group_hr_line_manager') or self.user_has_groups('topline.group_internal_audit'):
            is_manager = True
        self.is_manager = is_manager

    def _valid_field_parameter(self, field, name):
        # EXTENDS models
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    is_manager = fields.Boolean(compute='_check_user_group')
    state = fields.Selection(
        related='payment_requisition_form_id.state', store=True)
    name = fields.Char(string='Details/Purpose of Request', required=True)
    qty = fields.Float(string='Quantity', required=True, default=1)
    unit_price = fields.Float(string="Unit Price", required=True)
    amount_requested = fields.Float(
        string='Amount Requested', compute="_compute_requested_amount", required=True, tracking=True,)
    amount_approved = fields.Float(
        string='Amount Approved', copy=False, tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', states={
                                          'post': [('readonly', True)], 'done': [('readonly', True)]})
    account_id = fields.Many2one('account.account', string='Account', states={'post': [(
        'readonly', True)], 'done': [('readonly', True)]}, help="An Payment account is expected")
    
    def _compute_requested_amount(self):
        """Calculate the requested amount
        """
        for record in self:
            amount = 0
            if record.unit_price and record.qty:
                amount = record.unit_price * record.qty
            record.amount_requested = amount
