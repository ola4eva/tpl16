# -*- coding: utf-8 -*-

from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pprint
pp = pprint.PrettyPrinter(indent=4)


class payment_requisition(models.Model):
    _inherit = 'payment.requisition.form'

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

    @api.model
    def create(self, values):
        if values.get("payee_id"):
            payee_id = values.get("payee_id")
            is_md = self.is_md(payee_id)
            if is_md is True:
                values['state'] = "md_approve"
            elif is_md is False and values.get('md_request') is True:
                values["state"] = "md_approve"
        res = super(payment_requisition, self).create(values)
        return res

    @api.multi
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

    def button_md_approval_notification(self):
        user = self.env.user
        is_md = self.is_md(user.id)
        if not is_md and user.has_group("payment_requisition.approve_payment_for_md"):
            allowed_limit = user.company_id.md_proxy_approval_limit
            if self.total_amount_approved > allowed_limit:
                raise UserError(
                    "This amount is above your allowed limit. You are allowed to approve amounts up to %s!" % str(allowed_limit))
        return super(payment_requisition, self).button_md_approval_notification()

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

    @api.multi
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

    @api.multi
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
                        'analytic_account_id': line.analytic_account_id.id or requisition.default_analytic_account_id.id,
                        'date_maturity': date.today(),
                        'partner_id': requisition.payee_id.id,
                    }) for line in requisition.payment_requisition_form_line_ids] +

                    [(0, 0, {
                        'name': requisition.payee_id.name,
                        'credit': requisition.total_amount_approved > 0 and requisition.total_amount_approved,
                        'debit': 0.0,
                        'account_id': requisition.bank_journal_id.default_credit_account_id.id,
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
                        'analytic_account_id': requisition.default_analytic_account_id.id,
                        'date_maturity': date.today(),
                        'partner_id': requisition.payee_id.id,
                    })] +

                    [(0, 0, {
                        'name': requisition.payee_id.name,
                        'credit': amount > 0 and amount,
                        'debit': 0.0,
                        'account_id': requisition.bank_journal_id.default_credit_account_id.id,
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
            requisition._check_fully_paid()
        return True

    @api.multi
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

    @api.multi
    def button_finance_approval(self):
        res = super().button_finance_approval()
        for record in self:
            if any(line.amount_approved == False for line in record.payment_requisition_form_line_ids):
                raise UserError(
                    _("No approved amount on some lines."))
            else:
                return res


class PaymentRequisitionReject(models.Model):
    _name = 'payment.requisition.rejection.log'
    _description = 'Payment Requisition Rejection Log'

    requisition_id = fields.Many2one(
        comodel_name='payment.requisition.form', string='Requisition')
    reason = fields.Char(string='Reason')
    user_id = fields.Many2one(comodel_name='res.users', string='Rejected By')
    datetime_rejection = fields.Datetime('Date')


class AccountJournal(models.Model):

    _inherit = 'account.move'

    requisition_id = fields.Many2one(
        "payment.requisition.form", "Payment Requisition")

    def action_post(self):
        res = super(AccountJournal, self).action_post()
        if self.requisition_id:
            requisition = self.env['payment.requisition.form'].search(
                [('payment_ids', 'in', [self.id])], limit=1)
            if not requisition:
                requisition = self.requisition_id
            if requisition:
                requisition._confirm_post()
        return res
