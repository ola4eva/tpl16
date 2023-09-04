# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _order = 'create_date DESC'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('submit', 'Submitted'),
        ('line_approve', 'Line Manager Approved'),
        ('internal_approve', 'Internal Audit Approved'),
        ('md_approve', 'MD Approved'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    num_word = fields.Char(string="Amount In Words:",
                           compute='_compute_amount_in_word')

    expectecd_delivery_date = fields.Date(string='Expected Delivery Date')
    atp_id = fields.Many2one(comodel_name='atp.form', string='ATP Form')

    order_line = fields.One2many(comodel_name="purchase.order.line", inverse_name="order_id",
                                 readonly=True, states={'draft': [('readonly', False)], 'md_approve': [('readonly', False)]})

    
    def button_submit(self):
        self.write({'state': 'submit'})
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "RFQ {} for {} needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    def _default_owner(self):
        return self.env.context.get('default_employee_id') or self.env['res.users'].browse(self.env.uid).partner_id

    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    owner_id = fields.Many2one('res.partner', 'Owner',
                               states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=_default_owner,
                               help="Default Owner")

    employee_id = fields.Many2one('hr.employee', 'Requesting Employee',
                                  states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=_default_employee,
                                  help="Default Owner")

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
    active = fields.Boolean(string='Active?', default=True)

    
    def button_line_manager_approval(self):
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
        subject = "RFQ '{}', for {} has been approved by supervisor and need approval from internal Audit".format(
            self.name, self.employee_id.name)
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
        subject = "RFQ '{}', for '{}' has been approved by Audit needs approval from MD".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    
    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "RFQ '{}', for {} has been rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    
    def button_md_approval_notification(self):
        """Notify Finance team of MD's approval...
        """
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'account.group_account_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Purchase Order '{}', for '{}' has been approved by MD and needs action from Finance".format(
            self.name,  self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    
    def button_md_approval(self):
        """Managing director approves purchase order and notification is sent to finance
        """
        for order in self:
            if order.state not in ['internal_approve']:
                continue
            order.md_approval_date = date.today()
            order.md_approval = self._uid
            order.button_md_approval_notification()
            order.write({
                'state': 'md_approve'
            })
        return True

    
    def button_confirm(self):
        for order in self:
            if order.state not in ['md_approve']:
                continue
            subject = "Payment Order '{}' has been approved by Finance".format(order.name)
            partner_ids = []
            for partner in self.message_partner_ids:
                partner_ids.append(partner.id)
            employee_partner = self.employee_id.user_id and self.employee_id.user_id.partner_id.ids or []
            if employee_partner:
                partner_ids.extend(employee_partner)
            self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
            order._add_supplier_to_product()
            order.button_approve()
        return True

    
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(
                rec.amount_total)) + ' only'


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_qty = fields.Float(states={'md_approve': [('readonly', False)]})
    price_unit = fields.Float(states={'md_approve': [('readonly', False)]})
