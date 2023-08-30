from datetime import date
from ast import literal_eval
from odoo import models, fields, api


class ServiceOrder(models.Model):
    _name = "service.order"
    _description = 'Service Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('line_manager', 'Line Manager Approval'),
        ('qaqc', 'QA/QC Verification'),
        ('procurement', 'Procurement Approval'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Requested by', default=_default_employee)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', related='employee_id.department_id')
    location = fields.Char(string='Location')
    project_id = fields.Many2one(
        comodel_name='project.project', string='Project')
    project_description = fields.Char(string='Project Description')
    date = fields.Date(string='Date', default=date.today())

    service_order_line_ids = fields.One2many(
        'service.order.line', 'service_order_id', string="Service Order", copy=True)

    line_manager_approval = fields.Many2one(
        'res.users', 'Manager Name', readonly=True, track_visibility='onchange')
    line_manager_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    procurement_approval = fields.Many2one(
        'res.users', 'Procurement Personnel Name', readonly=True, track_visibility='onchange')
    procurement_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    qaqc_approval = fields.Many2one(
        'res.users', 'QAQC Personnel Name', readonly=True, track_visibility='onchange')
    qaqc_approval_date = fields.Date(
        string='QAQC Ver. Date', readonly=True, track_visibility='onchange')

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    payment_req_count = fields.Integer(
        compute="_payr_count", string="Payment Requisitions", store=False)
    po_count = fields.Integer(
        compute="_po_count", string="RFQ's/PO's", store=False)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'service.order') or '/'
        return super(ServiceOrder, self).create(vals)

    
    def button_submit(self):
        self.write({'state': 'line_manager'})
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Service Order '{}' needs approval".format(self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        # self.alert_hr()
        return False

    
    def button_submit_to_qa_qc(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_qa')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Service Order '{}' needs approval from QA/QC".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    
    def button_submit_to_procurement(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'purchase.group_purchase_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Service Order '{}' needs approval from procurement".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    
    def alert_hr(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'hr.group_hr_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Service Order '{}' has been created, please review".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    
    def action_line_manager_approval(self):
        self.write({'state': 'qaqc'})
        self.line_manager_approval_date = date.today()
        self.line_manager_approval = self._uid
        subject = "Service Order {} has been approved by Line Manager".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_to_qa_qc()

    
    def action_qaqc_approval(self):
        self.write({'state': 'procurement'})
        self.qaqc_approval_date = date.today()
        self.qaqc_approval = self._uid
        subject = "Service Order {} has been approved by QAQC".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_to_procurement()

    
    def button_procurement_approval(self):
        self.write({'state': 'approve'})
        self.procurement_approval_date = date.today()
        self.procurement_approval = self._uid
        subject = "Service Order {} has been approved by Procurement".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Service {} has been Rejected".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    
    def create_purchase_order2(self):
        """
        Method to open create atp form
        """
        view_ref = self.env['ir.model.data'].get_object_reference(
            'purchase', 'purchase_order_form')
        view_id = view_ref[1] if view_ref else False
        for subscription in self:
            order_lines = []
            for line in subscription.service_order_line_ids:
                order_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_id': line.product_id.id,
                    'account_id': line.product_id.property_account_expense_id.id,
                    'product_qty': line.qty,
                    'date_planned': date.today(),
                    'price_unit': line.product_id.standard_price,
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
        view_ref = self.env['ir.model.data'].get_object_reference(
            'topline', 'topline_payment_requisition_form_view')
        view_id = view_ref[1] if view_ref else False
        for subscription in self:
            order_lines = []
            for line in subscription.service_order_line_ids:
                if line.product_id:
                    name = line.product_id.name + ': ' + line.description
                else:
                    name = line.description
                order_lines.append((0, 0, {
                    'name': name,
                    'amount_requested': line.product_id.standard_price * line.qty,
                }))

        res = {
            'type': 'ir.actions.act_window',
            'name': ('Payment Requisition'),
            'res_model': 'payment.requisition.form',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {'default_source': self.name, 'default_date': date.today(), 'default_service_order_id': self.id, 'default_payment_requisition_form_line_ids': order_lines}
        }

        return res

    
    def _payr_count(self):
        oe_po = self.env['payment.requisition.form']
        for pa in self:
            domain = [('atp_id', '=', pa.id)]
            pres_ids = oe_po.search(domain)
            pres = oe_po.browse(pres_ids)
            payment_req_count = 0
            for pr in pres:
                payment_req_count += 1
            pa.payment_req_count = payment_req_count
        return True

    
    def _po_count(self):
        oe_po = self.env['purchase.order']
        for pa in self:
            domain = [('atp_id', '=', pa.id)]
            pres_ids = oe_po.search(domain)
            pres = oe_po.browse(pres_ids)
            po_count = 0
            for pr in pres:
                po_count += 1
            pa.po_count = po_count
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
            'topline.topline_payment_requisition_form_action').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('atp_id', '=', self.id))
        return action


class ServiceOrderLine(models.Model):
    _name = "service.order.line"
    _description = 'Service Order Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    service_order_id = fields.Many2one('service.order', 'Service Order')

    product_id = fields.Many2one(
        comodel_name='product.product', string='Product')
    description = fields.Char(string='DESCRIPTION', required=True)
    serial_no = fields.Char(string='EQUIPMENT SERIAL NO./ ASSET NO.')
    qty = fields.Float(string='QTY', required=True)

