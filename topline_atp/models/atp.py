# -*- coding: utf-8 -*-

from datetime import date
from ast import literal_eval
from odoo import api, fields, models, _


class ATPform(models.Model):
    _name = 'atp.form'
    _description = 'Authorization to Purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('approve', 'QA/QC Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    atp_form_line_ids = fields.One2many(
        'atp.form.lines', 'atp_form_id', string="ATP Form Lines", copy=True)

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')
    date = fields.Date(string='Date', required=True,
                       tracking=True, default=date.today())
    project_des = fields.Char(string='Project Title',
                              required=True, tracking=True)
    project_id = fields.Many2one(
        comodel_name='project.project', string='Relating Project', tracking=True)
    remark = fields.Char(string='Remark', required=False)
    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking', string='Inventory Operation', tracking=True)

    expected_date = fields.Date(
        string='Expected Date of Arrival', tracking=True)

    total = fields.Float(string='Total', compute='_total_unit', readonly=True)

    po_count = fields.Integer(
        compute="_po_count", string="RFQ's/PO's", store=False)

    payment_req_count = fields.Integer(
        compute="_payr_count", string="Payment Requisitions", store=False)

    stock_source = fields.Char(string='Source', copy=False)

    def name_get(self):
        res = []
        for atp in self:
            result = atp.name
            if atp.stock_source:
                result = str(atp.name) + " " + "-" + \
                    " " + str(atp.stock_source)
            res.append((atp.id, result))
        return res

    def create_purchase_order(self):
        """
        Method to open create purchase order form
        """

        view_ref = self.env['ir.model.data'].get_object_reference(
            'purchase', 'purchase_order_form')
        view_id = view_ref[1] if view_ref else False

        # purchase_line_obj = self.env['purchase.order.line']
        for subscription in self:
            order_lines = []
            for line in subscription.atp_form_line_ids:
                order_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_id': line.product_id.id,
                    'account_id': line.product_id.property_account_expense_id.id,
                    # 'account_analytic_id': 1,
                    'product_qty': line.qty,
                    'date_planned': date.today(),
                    'price_unit': line.price,
                }))

        res = {
            'type': 'ir.actions.act_window',
            'name': ('Purchase Order'),
            'res_model': 'purchase.order',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {
                'default_stock_source': self.name,
                'default_order_line': order_lines,
                'default_atp_id': self.id,
            }
        }

    def create_purchase_order2(self):
        """
        Method to open create atp form
        """

        # partner_id = self.client_id
        # client_id = self.client_id
        # store_request_id = self.id
        # sub_account_id = self.sub_account_id
        # product_id = self.move_lines.product_id

        view_ref = self.env['ir.model.data'].check_object_reference(
            'purchase', 'purchase_order_form')
        view_id = view_ref[1] if view_ref else False

        for subscription in self:
            order_lines = []
            for line in subscription.atp_form_line_ids:
                order_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_id': line.product_id.id,
                    # 'account_id': line.product_id.property_account_expense_id.id,
                    'product_qty': line.qty,
                    'date_planned': date.today(),
                    'price_unit': line.price,
                }))

        res = {
            'type': 'ir.actions.act_window',
            'name': ('Purchase Order'),
            'res_model': 'purchase.order',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {'default_stock_source': self.name, 'default_atp_id': self.id, 'default_order_line': order_lines}
        }

        return res

    def create_payment_requisition(self):
        """
        Method to open create payment requisition
        """
        view_ref = self.env['ir.model.data'].check_object_reference(
            'topline_payment_requisition', 'topline_payment_requisition_form_view')
        view_id = view_ref[1] if view_ref else False

        for subscription in self:
            order_lines = []
            for line in subscription.atp_form_line_ids:
                order_lines.append((0, 0, {
                    'name': line.name,
                    'qty': line.qty,
                    'amount_requested': line.price_subtotal,
                }))

        res = {
            'type': 'ir.actions.act_window',
            'name': ('Payment Requisition'),
            'res_model': 'payment.requisition.form',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {'default_source': self.name, 'default_date': date.today(), 'default_atp_id': self.id, 'default_payment_requisition_form_line_ids': order_lines}
        }

        return res

    def _po_count(self):
        purchase_order = self.env['purchase.order']
        for atp in self:
            domain = [('atp_id', '=', atp.id)]
            atp.po_count = purchase_order.search_count(domain)
        return True

    def _payr_count(self):
        payment_requisition = self.env['payment.requisition.form']
        for atp in self:
            domain = [('atp_id', '=', atp.id)]
            atp.payment_req_count = payment_requisition.search_count(domain)
        return True

    def open_po(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('atp_id', '=', self.id))
        return action

    def open_payr(self):
        self.ensure_one()
        action = self.env.ref(
            'topline_payment_requisition.topline_payment_requisition_form_action').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('atp_id', '=', self.id))
        return action

    @api.depends('atp_form_line_ids.price')
    def _total_unit(self):
        self.total = 0
        for line in self.atp_form_line_ids:
            self.total += line.price_subtotal

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'atp.form') or '/'
        return super(ATPform, self).create(vals_list)

    def button_submit(self):
        self.write({'state': 'submit'})
        group_id = self.env.ref(
            'quality.group_quality_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Authorization to Purchase '{}' needs approval".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    def button_approval(self):
        self.write({'state': 'approve'})
        group_id = self.env.ref(
            'purchase.group_purchase_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Authorization to Purchase '{}' has been approved".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Authorization to Purchase '{}' has been Rejected".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class ATPformLines(models.Model):
    _name = 'atp.form.lines'
    _description = 'ATP Form Lines'

    atp_form_id = fields.Many2one(comodel_name='atp.form', string='ATP Frm')

    product_id = fields.Many2one(
        comodel_name='product.product', string='Product')
    name = fields.Char(string='ASset/Material Name', required=True)
    qty = fields.Float(string='Quantity', required=True)
    model = fields.Char(string='Model', required=False)

    size = fields.Char('Size', copy=False)
    brand_id = fields.Many2one('brand.type', 'Make/Brand', copy=False)
    certificate_required = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Certificate Required', readonly=False, index=True, copy=False, tracking=True,)

    price = fields.Float(string='Est. Price', required=False)

    def _valid_field_parameter(self, field, name):
        # EXTENDS models
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    @api.onchange('product_id')
    def _onchange_partner_id(self):
        self.name = self.product_id.name
        self.price = self.product_id.standard_price

    price_subtotal = fields.Float(
        string='Est. Price Subtotal', readonly=True, compute='_price_subtotal')

    def _price_subtotal(self):
        for line in self:
            self.price_subtotal = line.price * line.qty
