# -*- coding: utf-8 -*-

from datetime import date
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class ExpenseRef(models.Model):
    _name = 'hr.expense'
    _inherit = 'hr.expense'
    _order = 'create_date DESC'

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')
    description = fields.Char(string='Expense Desciption')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hr.expense') or '/'
        return super(ExpenseRef, self).create(vals_list)


class HrExpenseSheet(models.Model):
    _name = "hr.expense.sheet"
    _inherit = 'hr.expense.sheet'
    _order = 'create_date DESC'

    state = fields.Selection([('submit', 'Submitted'),
                              ('line_approval', 'Line Manager Approved'),
                              ('audit', 'Internal Review'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('open', 'Open'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='submit', required=True,
                             help='Expense Report State')

    name = fields.Char(string='Expense Report Summary',
                       readonly=True, required=True)
    description = fields.Char(
        string='Expense Desciption', readonly=True, compute='get_desc')

    def get_desc(self):
        for expense in self.expense_line_ids:
            if expense.description:
                self.description = expense.description
                break

    '''
    
    def button_line_manager_approval(self):
        self.write({'state': 'line_approval'})
        subject = "Expense '{}' has been approved by Line Manager".format(self.name)
        partner_ids = []
        for partner in self.sheet_id.message_partner_ids:
            partner_ids.append(partner.id)
        self.sheet_id.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return {}
    '''

    def button_md_approval(self):
        self.write({'state': 'approve'})
        subject = "Expense '{}' has been approved by MD".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return {}

    def button_audit_approval(self):
        self.write({'state': 'audit'})
        subject = "Expense '{}' has been approved by Audit".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return {}

    def expense_audit_approval_notification(self):
        group_id = self.env.ref(
            'topline.group_internal_audit')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Expense '{}' needs approval".format(self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False
    '''
    
    def expense_audit_approval_notification(self):
        subject = "Expense '{}' has been approved".format(self.name)
        partner_ids = []
        for partner in self.sheet_id.message_partner_ids:
            partner_ids.append(partner.id)
        self.sheet_id.message_post(subject=subject,body=subject,partner_ids=partner_ids)
    '''

    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(
                _("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot approve your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(
                    _("You can only approve your department expenses"))

        responsible_id = self.user_id.id or self.env.user.id
        self.write({'state': 'line_approval', 'user_id': responsible_id})
        self.activity_update()
        # self.expense_audit_approval_notification()

    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(
                _("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(
                _("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
            self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        self.filtered(lambda hol: hol.state == 'line_approval').activity_feedback(
            ['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state == 'cancel').activity_unlink(
            ['hr_expense.mail_act_expense_approval'])
