from datetime import date 
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CashRetirementForm(models.Model):
    _name = 'cash.retirement.form'
    _description = 'Cash Retirement Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'
    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('line_approve', 'Line Manager Approved'),
        ('internal_approve', 'Internal Audit Approved'),
        ('md_approve', 'MD Approved'),
        ('approve', 'Finance Approved'),
        ('reject', 'Reject'),
        ], string='Status', readonly=False, 
        index=True, copy=False, default='draft', 
        tracking=True)

    def _default_department(self): 
        """this method is to search the hr.employee 
        and return the user id of the person clicking the form atm
        """
        user = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        return user.department_id.id
    
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        return self.env['hr.employee'].search([('user_id','=',self.env.uid)])
    
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
    
    
    def _check_manager_approval(self):
        current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id
        if self.employee_id.user_id == self.env.user:
            raise UserError(_("You cannot approve your own Request"))

        if not self.env.user in current_managers:
            raise UserError(_("You can only approve your department expenses"))
    
    cash_retirement_form_line_ids = fields.One2many('cash.retirement.form.lines', 'cash_retirement_form_id', string="cash retirement form lines", copy=True)
    
    date = fields.Date(string='Date', required=True, tracking=True)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department', default=_default_department)
    project_description = fields.Char(string='Project Description',  tracking=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', required=True, string='Name of Payee', default=_default_employee, tracking=True)
    currency_id = fields.Many2one(comodel_name='res.currency', required=True, string='Currency', default=_default_currency, tracking=True)
    location = fields.Char(string='location',  tracking=True)
    
    total_amount_requested = fields.Float(string='Total amount requested', compute='_total_amount_requested', readonly=True,)
    total_amount_approved = fields.Float(string='Total amount approved', compute='_total_amount_approved', readonly=True,)
    
    num_word = fields.Char(string="Amount In Words:", compute='_compute_amount_in_word')
    
    employee_name = fields.Many2one('res.users','Employee Name', readonly=True, tracking=True)
    employee_approval_date = fields.Date(string='Date', readonly=True, tracking=True)
    
    supervisor_approval = fields.Many2one('res.users','Supervisor Name', readonly=True, tracking=True)
    supervisor_approval_date = fields.Date(string='Date', readonly=True, tracking=True)
    
    audit_approval = fields.Many2one('res.users','Auditors Name', readonly=True, tracking=True)
    audit_approval_date = fields.Date(string='Date', readonly=True, tracking=True)
    
    finance_comments = fields.Char(string='Comments', tracking=True)
    finance_approval = fields.Many2one('res.users','Finance Name', readonly=True, tracking=True)
    finance_approval_date = fields.Date(string='Date', readonly=True, tracking=True)
    
    received_approval = fields.Many2one('res.users','Recipients Name',  tracking=True)
    received_approval_date = fields.Date(string='Date', tracking=True)
    name = fields.Char('Order Reference', readonly=True, required=True, index=True, copy=False, default='New')
    paid = fields.Boolean(string="Paid")
    advance_id = fields.Many2one(comodel_name="cash.advance.request.form", string="Cash Advance")
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal")
    move_id = fields.Many2one(comodel_name="account.move", string="Journal Entry")

    def post_entries(self):
        """Post the entries into the respective accounts.
        The accounting entries are as follows:

        Say the advance amount = #5,000

        Case 1: Exact advance amount was expended:
        Expense = #5,000

        Description       |  Debit  | Credit
        ------------------------------------
        Partner Receivable|  0      | 5,000
        Expense Account   |  5,000  | 0
        ------------------------------------
                          |  5,000  | 5,000

        Case 2: Expense amount is less than advance amount,
        and the staff will need to return some money to a refund account.
        Expense = #4,000

        Description       |  Debit  | Credit
        ------------------------------------
        Partner Receivable|  0      | 5,000
        Refund Account    |  1,000  | 0
        Expense Account   |  4,000  | 0
        ------------------------------------
                          |  5,000  | 5,000
        ------------------------------------
        Case 3: Exact advance amount is greater than adcance amount: in this case
        the company needs to pay the staff the additional expense. This requires a
        payment to be initiated against the employee account.
        Expense = #6,000

        Description       |  Debit  | Credit
        ------------------------------------
        Partner Receivable|  0      | 5,000
        Partner Payable   |  0      | 1,000
        Expense Account   |  6,000  | 0
        ------------------------------------
                          |  5,000  | 5,000
        ------------------------------------
        """
        # Handle case 1
        requesting_partner = self.employee_id.user_id.partner_id
        move_vals = {
            'ref': self.name,
            'date': date.today(),
            'journal_id': self.journal_id.id,
            'line_ids': [(0,0, {
                'name': self.name,
                'debit': line.amount_approved > 0 and line.amount_approved,
                'credit': 0.0,
                'account_id': line.account_id.id, # Debit employee receivable
                'date_maturity': date.today(),
                'partner_id': requesting_partner.id,
            }) for line in self.cash_retirement_form_line_ids] + [(0,0, {
                    'name': self.name,
                    'credit': self.total_amount_approved > 0 and self.total_amount_approved,
                    'debit': 0.0,
                    'account_id': requesting_partner.property_account_receivable_id.id,
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
        print("**** Posting entries from cash retirement ****")
        self.paid = False
        return True

    @api.onchange('advance_id')
    def _onchange_advance_id(self):
        if self.advance_id:
            # update advance amount
            amount_advance = self.advance_id.amount_approved

   
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('cash.retirement') or '/'
        return super(CashRetirementForm, self).create(vals_list)
    
    
    def button_submit(self):
        self.write({'state': 'submit'})
        self.employee_approval_date = date.today()
        self.employee_name = self._uid
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Cash Retirement '{}' for {} needs approval".format(self.name, self.employee_id.name)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return False
    
    
    def button_line_manager_approval(self):
        self._check_manager_approval()
        self.write({'state':'line_approve'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object('topline.group_internal_audit')
        partner_ids = []
        user_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Cash Retirement '{}' for {} has been approved by supervisor".format(self.name, self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        
    
    def button_audit_approval_notification(self):
        self.write({'state':'internal_approve'})
        self.audit_approval_date = date.today()
        self.audit_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object('topline.group_finance_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Cash Retirement '{}' for '{}' needs approval".format(self.name, self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
    
    
    def button_md_approval_notification(self):
        self.write({'state':'md_approve'})
        self.md_approval_date = date.today()
        self.md_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object('account.group_account_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Cash Retirement '{}' for '{}' has been approved by MD and needs approval from Finance".format(self.name, self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
    
    
    def button_finance_approval(self):
        self.write({'state':'approve'})
        self.finance_approval_date = date.today()
        self.finance_approval = self._uid
        subject = "Cash Retirement '{}' for {} has been approved by Finance".format(self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
    
    
    def button_reject(self):
        self.write({'state':'reject'})
        subject = "Cash Retirement '{}' for {} has been rejected".format(self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
    
    
    @api.depends('cash_retirement_form_line_ids.amount_requested')
    def _total_amount_requested(self):
        self.total_amount_requested = 0
        for line in self.cash_retirement_form_line_ids:
            self.total_amount_requested += line.amount_requested
    
    
    @api.depends('cash_retirement_form_line_ids.amount_approved')
    def _total_amount_approved(self):
        self.total_amount_approved = 0
        for line in self.cash_retirement_form_line_ids:
            self.total_amount_approved += line.amount_approved
    
    
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(rec.total_amount_approved)) + ' only'
    
class CashRetirementFormLines(models.Model):
    _name = 'cash.retirement.form.lines'
    _description = 'Cash Retirement Form Lines'
    
    cash_retirement_form_id = fields.Many2one(comodel_name='cash.retirement.form', string='cash retirement form')
    
    name = fields.Char(string='DETAILS OF ADVANCE ON EXPENDITURE', required=True)
    account_id = fields.Many2one(comodel_name="account.account", string='ACCOUNT')
    note = fields.Char(string='DESCRIPTION')
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string='ANALYTIC ACCOUNT')
    amount_requested = fields.Float(string='AMOUNT', required=True)
    amount_approved = fields.Float(string='AMOUNT APPROVED')

