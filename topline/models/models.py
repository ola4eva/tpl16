# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from ast import literal_eval
from odoo.tools import float_compare


class ConstructionEquipmentChecklist(models.Model):
    _name = "construction.equipment.checklist"
    _description = 'CONSTRUCTION EQUIPMENT CHECKLIST'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    @api.model
    def _get_default_project(self):
        ctx = self._context
        if ctx.get('active_model') == 'project.project':
            return self.env['project.project'].browse(ctx.get('active_ids')[0]).id

    state = fields.Selection([
        ('draft', 'New'),
        ('supervisor', 'Supervisor'),
        ('manager', 'Manager'),
        ('store', 'Store'),
        ('qa_qc', 'QA/QC'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    name = fields.Char(string='Name')
    job_location = fields.Char(string='Job Location')
    project_id = fields.Many2one(comodel_name='project.project',
                                 string='Project', readonly=False, default=_get_default_project)
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee/Owner', default=_default_employee)
    construction_equpiment_line_ids = fields.One2many(
        'construction.equipment.checklist.line', 'construction_equpiment_line_id', string="Action Move", copy=True)
    date = fields.Date(string='Date', default=date.today())
    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    manager_approval = fields.Many2one(
        'res.users', 'Manager Name', readonly=True, track_visibility='onchange')
    manager_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    store_approval = fields.Many2one(
        'res.users', 'Store Personnel Name', readonly=True, track_visibility='onchange')
    store_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    qa_qc_approval = fields.Many2one(
        'res.users', 'QA/QC Personnel Name', readonly=True, track_visibility='onchange')
    qa_qc_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    @api.multi
    def button_submit(self):
        self.write({'state': 'supervisor'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_hr_line_manager')
        user_ids = []
        partner_ids = []
        # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
        for user in group_id.users:
            user_ids.append(user.id)
            # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "CONSTRUCTION EQUIPMENT CHECKLIST '{}' needs approval".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def action_line_manager_approval(self):
        self.write({'state': 'manager'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        subject = "CONSTRUCTION EQUIPMENT CHECKLIST {} has been approved by supervisor".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_store_approval(self):
        self.write({'state': 'store'})
        self.manager_approval_date = date.today()
        self.manager_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'stock.group_stock_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "CONSTRUCTION EQUIPMENT CHECKLIST '{}' needs approval from store".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def action_qa_qc_approval(self):
        self.write({'state': 'qa_qc'})
        self.store_approval_date = date.today()
        self.store_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'quality.group_quality_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "CONSTRUCTION EQUIPMENT CHECKLIST '{}' needs approval from QA/QC".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def action_approval(self):
        self.write({'state': 'approve'})
        self.qa_qc_approval_date = date.today()
        self.qa_qc_approval = self._uid
        subject = "CONSTRUCTION EQUIPMENT CHECKLIST {} has been approved by QA/QC".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "CONSTRUCTION EQUIPMENT CHECKLIST {} has been Rejected".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class ConstructionEquipmentChecklistLine(models.Model):
    _name = "construction.equipment.checklist.line"
    _description = 'CONSTRUCTION EQUIPMENT CHECKLIST LINE'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    construction_equpiment_line_id = fields.Many2one(
        'construction.equipment.checklist', 'Construction Equipment Checklist')

    product_id = fields.Many2one(
        comodel_name='product.product', string='ITEM', required=True)
    description = fields.Char(
        string='DESCRIPTION (make, type, size, asset code)', required=True)
    qty_mob = fields.Float(string='QTY MOB')
    qty_demob = fields.Float(string='QTY DEMOB')
    demob_remarks = fields.Char(string='DE-MOB REMARKS')


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

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Service {} has been Rejected".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
    def open_po(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('atp_id', '=', self.id))
        return action

    @api.multi
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


class ActionRequestLog(models.Model):
    _name = "action.request.log"
    _description = 'CORRECTIVE/PREVENTIVE ACTION LOG'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    @api.model
    def _get_default_project(self):
        ctx = self._context
        if ctx.get('active_model') == 'project.project':
            return self.env['project.project'].browse(ctx.get('active_ids')[0]).id

    partner_id = fields.Many2one(
        comodel_name='res.partner', related='project_id.partner_id', string='Customer', readonly=True)

    project_id = fields.Many2one(comodel_name='project.project',
                                 string='Project', readonly=False, default=_get_default_project)

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Owner', default=_default_employee)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', related='employee_id.department_id')

    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Open'),
        ('on_hold', 'On Hold'),
        ('closed', 'Closed'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    action_request_log_line_ids = fields.One2many(
        'action.request.log.line', 'action_request_log_id', string="Action Request Log Line", copy=True)
    date = fields.Date(string='Date', default=date.today())


class ActionRequestLogLine(models.Model):
    _name = "action.request.log.line"
    _description = 'CORRECTIVE/PREVENTIVE ACTION LOG Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    action_request_log_id = fields.Many2one(
        'action.request.log', 'Action Request Log')

    ar_no = fields.Char(string='AR No.')
    initiator_id = fields.Many2one(
        comodel_name='hr.employee', string='Initiator', required=True)
    date_initiated = fields.Date(
        string='Date Initiated', default=date.today(), required=True)
    description_of_problem = fields.Char(
        string='Description of Problem (Nonconformance / Potential Nonconformance)', required=True)
    root_cause = fields.Char(string='Root Cause', required=True)
    action_taken = fields.Char(string='Action Taken')
    date_closed = fields.Date(string='Date Closed')


class MaintenanceRequestAndFailureReportSheet(models.Model):
    _name = "maintenance.request.failure.report.sheet"
    _description = 'Maintenance Request And Failure Report Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

    state = fields.Selection([
        ('draft', 'New'),
        ('supervisor', 'Supervisor Approved'),
        ('qaqc', 'QA/QC Approved'),
        ('store', 'Store Approved'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    asset_id = fields.Many2one(
        comodel_name='account.asset.asset', string='Asset(s):')

    name = fields.Char(string='ASSET NAME:', required=True)
    asset_no = fields.Char(string='ASSET NO:')
    hour_odo_meter = fields.Char(string='HOUR/ODO-METER:')
    date = fields.Datetime(string='Date & Time:')
    project_id = fields.Many2one(
        comodel_name='project.project', string='PROJECT:')
    location = fields.Char(string='LOCATION:')
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='REPORTED BY:', default=_default_employee)
    employee_user = fields.Many2one(comodel_name='hr.employee', string='USER:')

    observations = fields.Char(string='OBSERVATIONS')
    action_taken = fields.Char(string='ACTION TAKEN')

    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    diagnosis = fields.Char(string='DIAGNOSIS:')
    causes = fields.Char(string='CAUSES:')
    repairs_done = fields.Char(string='REPAIRS DONE/TO BE DONE:')
    part_replaced = fields.Char(string='PARTS REPLACED/TO BE REPLACED:')

    repair_date = fields.Date(string='Repair Date:')
    cost_of_repair = fields.Monetary(string='Cost Of Repair:')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='By/Vendor:')
    job_supervised_by_id = fields.Many2one(
        comodel_name='hr.employee', String='Job Supervised By:')

    manager_approval = fields.Many2one(
        'res.users', 'Manager Name', readonly=True, track_visibility='onchange')
    manager_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    ref = fields.Char('Order Reference', readonly=False,
                      required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('ref', 'New') == 'New':
            vals['ref'] = self.env['ir.sequence'].next_by_code(
                'maintenance.request.failure.report.sheet') or '/'
        return super(MaintenanceRequestAndFailureReportSheet, self).create(vals)

    @api.onchange('asset_id')
    def _update_asset_fields(self):
        self.name = self.asset_id.name
        self.asset_no = self.asset_id.x_studio_asset_no

    @api.multi
    def button_submit(self):
        self.write({'state': 'supervisor'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_hr_line_manager')
        user_ids = []
        partner_ids = []
        # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
        # for user in group_id.users:
        #    user_ids.append(user.id)
        # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)=
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Maintenance Request And Failure Report Sheet '{}' needs approval".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def action_line_manager_approval(self):
        self.write({'state': 'approve'})
        self.manager_approval_date = date.today()
        self.manager_approval = self._uid
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        subject = "Maintenance Request And Failure Report Sheet {} has been approved by supervisor".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Maintenance Request And Failure Report Sheet {} has been Rejected".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class QAQCPremobilizationChecklist(models.Model):
    _name = "qaqc.premobilization.checklist"
    _description = 'QA/QC Premobilization Checklist (Onshore And Offshore)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one(
        comodel_name='project.project', string='Project Title')

    personnel_qaqc_premobilization_checklist_ids = fields.One2many(
        'personnel.qaqc.premobilization.checklist', 'qaqc_premobilization_checklist_id', string="PersonnelQA/QC Premobilization Checklist (Onshore And Offshore)", copy=True)
    equipment_accessories_qaqc_premobilization_checklist_ids = fields.One2many(
        'equipment.accessories.qaqc.premobilization.checklist', 'qaqc_premobilization_checklist_id', string=" Equipment & Accessories QA/QC Premobilization Checklist (Onshore And Offshore)", copy=True)
    equipment_loadout_qaqc_premobilization_checklist_ids = fields.One2many(
        'equipment.loadout.qaqc.premobilization.checklist', 'qaqc_premobilization_checklist_id', string="Equipment Load-Out QA/QC Premobilization Checklist (Onshore And Offshore)", copy=True)
    documentation_qaqc_premobilization_checklist_ids = fields.One2many(
        'documentation.qaqc.premobilization.checklist', 'qaqc_premobilization_checklist_id', string="QA/QC Premobilization Checklist (Onshore And Offshore)", copy=True)

    supervisor_approval = fields.Many2one(
        'res.users', 'Project Supervisor', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    manager_approval = fields.Many2one(
        'res.users', 'Project Manager', readonly=True, track_visibility='onchange')
    manager_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    store_approval = fields.Many2one(
        'res.users', 'QA/QC Officer', readonly=True, track_visibility='onchange')
    store_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    qa_qc_approval = fields.Many2one(
        'res.users', 'QA/QC Manager', readonly=True, track_visibility='onchange')
    qa_qc_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')


class PersonnelQAQCPremobilizationChecklist(models.Model):
    _name = "personnel.qaqc.premobilization.checklist"
    _description = 'Personnel QA/QC Premobilization Checklist (Onshore And Offshore)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    qaqc_premobilization_checklist_id = fields.Many2one(
        'qaqc.premobilization.checklist', 'QA/QC Premobilization Checklist (Onshore And Offshore)')

    requirement = fields.Selection([
        ('medicals', 'Medicals'),
        ('huet_sas', 'HUET/SAS'),
        ('osp', 'OSP'),
        ('bosiet', 'BOSIET'),
        ('swimming_pass', 'Swimming Pass'),
        ('competency_certificate', 'Competency Certificate'),
        ('drivers_license', 'Driver’s License'),
        ('hse', 'HSE Induction/ Confined Space Training'),
    ], string='REQUIREMENT', required=True)

    verify = fields.Boolean(string='Verify')
    check = fields.Boolean(string='Check')
    remark = fields.Char(string='Remark')


class EquipmentAccessoriesQAQCPremobilizationChecklist(models.Model):
    _name = "equipment.accessories.qaqc.premobilization.checklist"
    _description = 'Equipment & Accessories QA/QC Premobilization Checklist (Onshore And Offshore)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    qaqc_premobilization_checklist_id = fields.Many2one(
        'qaqc.premobilization.checklist', 'QA/QC Premobilization Checklist (Onshore And Offshore)')

    requirement = fields.Selection([
        ('sling', 'Sling and Shackles certification'),
        ('pad_eye', 'Pad Eye'),
        ('color_code', 'Current Color Code'),
        ('lifting_belt', 'Lifting Belt Certification'),
        ('pre_mob_cert', 'Pre-Mob Certifications'),
        ('gauges_recorders', 'Gauges and Recorders'),
        ('cert_conformity', 'Certificate of Conformity (Flow Meter)'),
        ('inspection_tag', 'Inspection Tag'),
        ('hose_cert', 'Hose Certification'),
    ], string='REQUIREMENT', required=True)

    verify = fields.Boolean(string='Verify')
    check = fields.Boolean(string='Check')
    remark = fields.Char(string='Remark')


class EquipmentLoadoutQAQCPremobilizationChecklist(models.Model):
    _name = "equipment.loadout.qaqc.premobilization.checklist"
    _description = 'Equipment Load-Out QA/QC Premobilization Checklist (Onshore And Offshore)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    qaqc_premobilization_checklist_id = fields.Many2one(
        'qaqc.premobilization.checklist', 'QA/QC Premobilization Checklist (Onshore And Offshore)')

    requirement = fields.Selection([
        ('equipment_strapped', 'Equipment properly strapped?'),
        ('extended_lose_load', 'No Extended Load/Loose Hanging Load?'),
        ('extinguishers_loaded', 'Extinguishers loaded'),
        ('whip_check', 'Whip-Check Loaded'),
        ('relevant_fitting', 'Relevant Fittings and Accessories'),
        ('complete_tool_box', 'Complete Tool Box'),
        ('additional_hand_tools', 'Additional Hand Tools'),
    ], string='REQUIREMENT', required=True)

    verify = fields.Boolean(string='Verify')
    check = fields.Boolean(string='Check')
    remark = fields.Char(string='Remark')


class DocumentationQAQCPremobilizationChecklist(models.Model):
    _name = "documentation.qaqc.premobilization.checklist"
    _description = 'Documentation QA/QC Premobilization Checklist (Onshore And Offshore)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    qaqc_premobilization_checklist_id = fields.Many2one(
        'qaqc.premobilization.checklist', 'QA/QC Premobilization Checklist (Onshore And Offshore)')

    requirement = fields.Selection([
        ('pep_wms', 'PEP/WMS'),
        ('hse_plan', 'HSE Plan'),
        ('jha_jsa_tsa', 'JHA/JSA/TSA'),
        ('daily_site_report', 'Daily Site Report'),
        ('weekly_report_form', 'Weekly Report Form'),
        ('client_feedback_form', 'Clients’ Feedback form'),
        ('store_transfer', 'Waybill/Store Transfer'),
        ('maintenance_request', 'Maintenance request & failure report form'),
        ('equipment_schedule', 'Equipment & Maintenance Schedule'),
    ], string='REQUIREMENT', required=True)

    verify = fields.Boolean(string='Verify')
    check = fields.Boolean(string='Check')
    remark = fields.Char(string='Remark')


class EmployeeRequisitionForm(models.Model):
    _name = "employee.requisition.form"
    _description = 'Employee Requisition Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('line_manager', 'Supervisor'),
        ('hr_manager', 'HR Manager'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', default=_default_department)
    job_id = fields.Many2one(comodel_name='hr.job', string='Job Title')
    no_personnel_required = fields.Integer(string='No. of Personnel Required')
    existing_staff_present_in_category = fields.Integer(
        string='Existing Staff at present in this category')
    location = fields.Char(string='Location (mention details)')
    type_of_appointment = fields.Char(string='Type of Appointment')
    temporary_duration = fields.Char(
        string='If contract/temporary, state duration')
    qualification_required = fields.Char(
        string='Educational/Professional Qualification Required')
    skill_required = fields.Char(string='Skills Required')
    experience_required = fields.Char(string='Experience Required')
    job_description = fields.Char(string='Job Description')
    resource_required_date = fields.Date(
        string='Date by which Resource is Required')
    vacancy_cause = fields.Char(
        string='Vacancy caused due to (Resignation / Work Load / Additional Assignments)')
    vacancy_filled_internally = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Can vacancy be filled through internal transfers/promotion etc?')
    benefits_to_accrue = fields.Char(
        string='Benefits to Accrue on Additional Appointment')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='PROPOSED BY:', default=_default_employee)
    line_manager_approval = fields.Many2one(
        comodel_name='res.users', string='Name of Approving Authority')

    suggestion_for_replacement = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Suggestion for replacement if possible')
    name_of_person = fields.Char(
        string='Name of Person you intend to replace with')
    statement_of_justification = fields.Char(
        string='Statement of Justification for Internal / External Recruitment :')
    salary_range = fields.Float(string='Range of Salary ')
    when_position_filled = fields.Date(
        string='When the position can be filled up')
    remarks = fields.Char(string='Remarks')

    hr_manager_approval = fields.Many2one(
        comodel_name='res.users', string='(Approval Of HEAD – HR)')

    def action_submit(self):
        self.state = "submit"

    def action_line_manager_approve(self):
        self.state = "line_manager"

    def action_hr_manager_approve(self):
        self.state = "hr_manager"

    def action_final_approve(self):
        if self.job_id:
            if self.job_id.state != "recruit":
                self.job_id.state = "recruit"
            self.job_id.write({
                "no_of_recruitment": self.no_personnel_required,
                "department_id": self.department_id.id,
                "hr_responsible_id": self.env.user.id,
                "user_id": self.env.user.id,
                "description": self.job_description
            })
        return self.write({'state': "approve"})

    def open_job_posting(self):
        action = self.env.ref('hr.action_hr_job').read()[0]
        action['context'] = dict(self.env.context)
        action['views'] = [(self.env.ref('hr.view_hr_job_form').id, 'form')]
        action['res_id'] = self.job_id.id
        return action


class InstrumentsCalibrationStatusLog(models.Model):
    _name = "instruments.calibration.status.log"
    _description = 'Instruments Calibration Status Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee', default=_default_employee)
    date = fields.Date(string='Date', default=date.today())
    instruments_calibration_status_line_ids = fields.One2many(
        comodel_name='instruments.calibration.status.log.line', inverse_name='instruments_calibration_status_id')


class InstrumentsCalibrationStatusLogLine(models.Model):
    _name = "instruments.calibration.status.log.line"
    _description = 'Instruments Calibration Status Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    instruments_calibration_status_id = fields.Many2one(
        comodel_name='instruments.calibration.status.log')

    product_id = fields.Many2one(
        comodel_name='product.product', string='Product/Equipmemt')
    type_of_calibration_log_id = fields.Many2one(
        comodel_name='type.calibration.log', string='Equipment Category', required=True)
    description = fields.Char(
        string='Description & other Identification', required=True)
    type_of_calibration = fields.Char(string='Type of Calibration Carried out')
    calibrated_by = fields.Many2one(
        comodel_name='hr.employee', string='Calibrated By')
    last_calibration_date = fields.Date(string='Date of last Calibration')
    next_calibration_date = fields.Date(string='Calibration Next Due')
    remarks = fields.Char(string='Remarks')


class WorkCompletionCertificate(models.Model):
    _name = "work.completion.certificate"
    _description = 'Work Completion Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('admin', 'Admin Approval'),
        ('md', 'MD Approval'),
        ('qa_qc', 'QA/QC Manager'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee', default=_default_employee)
    date = fields.Date(string='Date', default=date.today())

    po_ref_id = fields.Many2one(
        comodel_name='purchase.order', string='P.O Ref:')
    description_work_rendered = fields.Char(
        string='Brief Description of Work Rendered')
    date_of_completion = fields.Date(string='Date of Completion of Work')
    vendor_rep = fields.Char(string='Vendor Representative Name')
    vendor_rep_date = fields.Date(string='Vendor Representative Date')
    topline_authorized_rep = fields.Many2one(
        comodel_name='hr.employee', string='Topline Representative Name')
    topline_authorized_rep_date = fields.Date(
        string='Topline Representative Date')
    qa_qc_rep = fields.Many2one(
        comodel_name='hr.employee', string='Topline Representative Name')
    qa_qc_rep_date = fields.Date(string='Topline Representative Date')
    comment = fields.Char(string='Comment')

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'work.completion.certificate') or '/'
        return super(WorkCompletionCertificate, self).create(vals)

    @api.multi
    def button_submit(self):
        self.write({'state': 'submit'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'quality.group_quality_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Work Completion Certificate for '{}' needs approval".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_submit_to_md(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_md')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Work Completion Certificate for '{}' needs approval from MD".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_admin_approval(self):
        self.write({'state': 'md'})
        subject = "Work Completion Certificate for '{}' has been approved by Admin".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_to_md()

    @api.multi
    def button_md_approval(self):
        self.write({'state': 'approve'})
        subject = "Work Completion Certificate for '{}' has been approved by MD".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_qa_qc_approval(self):
        self.write({'state': 'approve'})
        subject = "Work Completion Certificate for '{}' has been approved by QA/QC".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Work Completion Certificate for '{}' has been Rejected".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class ElectricityUseMonitoring(models.Model):
    _name = "electricity.use.monitoring"
    _description = 'Electricity Use Monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('manager', 'Admin Manager'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee', default=_default_employee)
    date = fields.Date(string='Date', default=date.today())

    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                              ('5', 'May'), ('6', 'June'), ('7',
                                                            'July'), ('8', 'August'),
                              ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                             string='Month', track_visibility='onchange')
    date_of_purchase = fields.Date(
        string='Date of Purchase', track_visibility='onchange')
    quantity = fields.Float(string='Quantity', track_visibility='onchange')
    remark = fields.Char(
        string='Remarks (comment on trend status)', track_visibility='onchange')
    control_measure = fields.Char(
        string='Control Measure', track_visibility='onchange')

    @api.multi
    def button_submit(self):
        self.write({'state': 'manager'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_admin_manager')
        partner_ids = []
        for user in group_id.users:
            partner_ids.append(partner.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Electricity Use Monitoring needs approval".format()
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_approval(self):
        self.write({'state': 'approve'})
        subject = "Electricity Use Monitoring has been approved".format()
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Electricity Use Monitoring has been Rejected".format()
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class WaterUseMonitoring(models.Model):
    _name = "water.use.monitoring"
    _description = 'Water Use Monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('manager', 'Admin Manager'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee', default=_default_employee)
    date = fields.Date(string='Date', default=date.today())

    date_time = fields.Datetime(
        string='Date & Time', track_visibility='onchange')
    level = fields.Char(string='Level', track_visibility='onchange')
    week = fields.Char(string='Week', track_visibility='onchange')
    control_measure = fields.Char(
        string='Control Measure', track_visibility='onchange')
    remark = fields.Char(
        string='Remarks (comment on trend status)', track_visibility='onchange')

    @api.multi
    def button_submit(self):
        self.write({'state': 'manager'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_admin_manager')
        partner_ids = []
        for user in group_id.users:
            partner_ids.append(partner.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Water Use Monitoring needs approval".format()
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_approval(self):
        self.write({'state': 'approve'})
        subject = "Water Use Monitoring has been approved".format()
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Water Use Monitoring has been Rejected".format()
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class AssetMovementForm(models.Model):
    _name = "asset.movement.form"
    _description = 'Asset Movement Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('line_manager', 'Line Manager'),
        ('store', 'Store'),
        ('md', 'MD'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    requested_employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Requested by', default=_default_employee)
    store_employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Issued by')

    line_manager_approval = fields.Many2one(
        'res.users', 'Depts Manager Name', readonly=True, track_visibility='onchange')
    line_manager_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    store_approval = fields.Many2one(
        'res.users', 'Store Personnel Name', readonly=True, track_visibility='onchange')
    store_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    md_approval = fields.Many2one(
        'res.users', 'MD Name', readonly=True, track_visibility='onchange')
    md_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    source_location = fields.Char(string='Transfer From')
    dest_location = fields.Char(string='Transfer To')

    date_of_transfer = fields.Date(string='Date of Transfer')
    date_recieved = fields.Date(string='Date Recieved')

    reason_for_transfer = fields.Char(string='Reason for Transfer')

    asset_movement_line_ids = fields.One2many(
        'asset.movement.form.line', 'asset_movement_id', string="Asset Movement", copy=True)

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'asset.movement.form') or '/'
        return super(AssetMovementForm, self).create(vals)

    @api.multi
    def button_submit(self):
        self.write({'state': 'line_manager'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_hr_line_manager')
        user_ids = []
        partner_ids = []
        # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
        for user in group_id.users:
            user_ids.append(user.id)
            # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Asset Movement '{}' needs approval".format(self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_submit_to_store(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'stock.group_stock_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Asset Movement '{}' needs approval from store".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
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

    @api.multi
    def action_line_manager_approval(self):
        self.write({'state': 'store'})
        self.line_manager_approval_date = date.today()
        self.line_manager_approval = self._uid
        subject = "Asset Movement {} has been approved by Line Manager".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_to_store()

    @api.multi
    def button_md_approval(self):
        self.write({'state': 'approve'})
        self.md_approval_date = date.today()
        self.md_approval = self._uid
        subject = "Asset Movement {} has been approved by MD".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_store_approval(self):
        self.write({'state': 'md'})
        self.store_approval_date = date.today()
        self.store_approval = self._uid
        subject = "Asset Movement {} has been approved by store".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Asset Movement {} has been Rejected".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class AssetMovementFormLine(models.Model):
    _name = "asset.movement.form.line"
    _description = 'Asset Movement Form Line'

    asset_movement_id = fields.Many2one(
        comodel_name='asset.movement.form', string='asset movement form')

    asset_number = fields.Char(string='Asset Number')
    asset_description = fields.Char(string='Asset Description')
    dept = fields.Many2one(comodel_name='hr.department', string='Department')
    location = fields.Char(string='Location')


class WasteManagementForm(models.Model):
    _name = "waste.management.form"
    _description = 'Waste Management Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Validate'),
                                                         ('refuse', 'Refuse'), ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    waste_originator_name = fields.Char(string='Name')
    waste_originator_date = fields.Datetime(string='Date & Time')
    waste_originator_tel = fields.Char(string='Tel')

    qty = fields.Float(string='QTY (KG/LITRES')
    loading_point = fields.Char(string='Loading Point')
    waste_originator_remark = fields.Char(string='Remarks')

    waste_dispatcher_name = fields.Char(string='Name')
    waste_dispatcher_date = fields.Datetime(string='Date & Time')
    waste_dispatcher_tel = fields.Char(string='Tel')

    transporter_name = fields.Char(string='Name')
    transporter_vehicle_vessel_no = fields.Char(string='Vehicle/Vessel No:')
    transporter_tel = fields.Char(string='Tel')

    waste_reciever_name = fields.Char(string='Name')
    waste_reciever_contact_person = fields.Many2one(
        comodel_name='res.partner', string='Contact Person')
    waste_reciever_tel = fields.Char(string='Tel')
    waste_reciever_remark = fields.Char(string='Remarks')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'waste.management.form') or '/'
        return super(WasteManagementForm, self).create(vals)

    @api.multi
    def button_submit(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_hse')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Waste Management Form '{}' has been prepaeed".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False


class DriversHealthChecklist(models.Model):
    _name = "drivers.health.checklist"
    _description = 'Drivers Health Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date = fields.Date(string='Date', default=date.today())

    inspector_id = fields.Many2one(
        comodel_name='hr.employee', string='Inspector')
    supervisor_id = fields.Many2one(
        comodel_name='hr.employee', string='Supervisor')

    checklist_line_ids = fields.One2many(
        'drivers.health.checklist.line', 'checklist_id', string="Drivers Health Checklist", copy=True)


class DriversHealthChecklistLine(models.Model):
    _name = "drivers.health.checklist.line"

    checklist_id = fields.Many2one(
        comodel_name='drivers.health.checklist', string='Drivers Health Checklist')

    requirements = fields.Selection([
        ('vision', 'Vision'),
        ('Hearing', 'Hearing'),
        ('attention', 'Attention'),
        ('memory', 'Memory'),
        ('insight', 'Insight'),
        ('judgement', 'Judgement'),
        ('reaction', 'Reaction Time'),
        ('sensation', 'Sensation'),
        ('muscle', 'Muscle Power'),
        ('co_ordination', 'Co-ordination'),
        ('blood_pressure', 'Blood Pressure'),
        ('alcohol_drugs', 'Alcohol & Drugs'),
    ], string='Requirements', readonly=False, index=True, copy=True,  track_visibility='onchange')

    result = fields.Char(string='Result')


class JobSafetyInspectionChecklist(models.Model):
    _name = "job.safety.inspection.checklist"
    _description = 'Job Safety Inspection Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    client_id = fields.Many2one(comodel_name='res.partner', string='Client')
    location = fields.Char(string='Location')
    inspection_id = fields.Many2one(
        comodel_name='hr.employee', string='Inspected By:')
    date = fields.Date(string='Date', default=date.today())

    posting_pressure = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                        string='Posting of Pressure and other work site warning Posters', copy=True,  track_visibility='onchange')
    safety_meeting = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                      string='. Are Safety Meetings conducted periodically? Date of last meeting?', copy=True,  track_visibility='onchange')
    first_aid_box = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                     string='First Aid Box and equipment properly stocked', copy=True,  track_visibility='onchange')
    site_injury_record = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                          string='Are work site injury records being kept?', copy=True,  track_visibility='onchange')
    emergency_tel = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                     string='Are emergency telephone numbers clearly posted?', copy=True,  track_visibility='onchange')
    emergency_info_posted = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                             string='Is the EMERGENCY INFORMATION form posted?', copy=True,  track_visibility='onchange')
    describe_violation = fields.Char(
        string='Describe any Violation – Location – Remedy Taken', copy=True,  track_visibility='onchange')

    emergency_lights = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                        string='Are emergency lights fully operational?     ', copy=True,  track_visibility='onchange')
    general_neatness = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                        string='Is there general neatness of the working areas?', copy=True,  track_visibility='onchange')
    regular_disposal_waste = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                              string='Is there a process for regular disposal of waste and trash?', copy=True,  track_visibility='onchange')
    passageways_walkways = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                            string='Are all passageways and walkways clear?', copy=True,  track_visibility='onchange')
    waste_container_usage = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                             string='Are waste containers provided and used by every crew member?', copy=True,  track_visibility='onchange')
    job_sanitary_facilities = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                               string='Are the Job Site’s sanitary facilities adequate and clean?', copy=True,  track_visibility='onchange')
    adequate_water_supply = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                             string='Is there adequate supply of water?', copy=True,  track_visibility='onchange')
    adequate_lighting = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                         string='Is there adequate lighting [in the event of night jobs]?', copy=True,  track_visibility='onchange')
    handrails_good = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                      string='Are handrails and stair treads in good condition? ', copy=True,  track_visibility='onchange')
    smoking_restrictions = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                            string='Is smoking restricted to certain locations? ', copy=True,  track_visibility='onchange')
    electrical_cords_good = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                             string='Are electrical cords and plugs in good condition?', copy=True,  track_visibility='onchange')
    circuit_breakers_free = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                             string='Are electric circuit breakers free of obstructions?', copy=True,  track_visibility='onchange')
    violations_description = fields.Char(
        string='Describe any Violation – Location – Remedy Taken', copy=True,  track_visibility='onchange')

    fire_instructions = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                         string='Have Fire instructions been given to crew members? ', copy=True,  track_visibility='onchange')
    fire_extinguishers = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                          string='Are Fire extinguishers identified, accessible, and fully charged? ', copy=True,  track_visibility='onchange')
    no_smoking_signs = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                        string='Are “No Smoking” signs posted and enforced where needed?', copy=True,  track_visibility='onchange')
    work_area_tidy = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                      string='Is the work area clean and tidy?    ', copy=True,  track_visibility='onchange')
    handling_flammables = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                           string='Is the Storage, use and handling of flammable liquids properly done', copy=True,  track_visibility='onchange')
    fire_hazards_checked = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                            string='Have all Fire hazards been checked and identified?', copy=True,  track_visibility='onchange')
    diesel_contained_properly = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('n_a', 'N/A')],
                                                 string='Is diesel contained in properly marked containers and locations?', copy=True,  track_visibility='onchange')
    fire_violations = fields.Char(
        string='Describe any Violation – Location – Remedy Taken', copy=True,  track_visibility='onchange')


class JobCallOutForm(models.Model):
    _name = "job.call.out.form"
    _description = 'Job Call Out Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    client = fields.Many2one(comodel_name='res.partner', string='Client')
    job_type = fields.Char(string='Job Type')
    location = fields.Char(string='Location')
    est_job_start = fields.Date(string='Estimated Job Start Day')
    engineer_in_charge = fields.Many2one(
        comodel_name='hr.employee', string='Engineer-In-Charge')
    supervisor = fields.Many2one(
        comodel_name='hr.employee', string='Supervisor')
    operator_1 = fields.Many2one(
        comodel_name='hr.employee', string='Operator 1')
    mechanic = fields.Many2one(comodel_name='hr.employee', string='Mechanic')
    operator_2 = fields.Many2one(
        comodel_name='hr.employee', string='Operator 2')
    operator_3 = fields.Many2one(
        comodel_name='hr.employee', string='Operator 3')
    trainee = fields.Many2one(
        comodel_name='hr.employee', string='Trainee (Engr/Operator): ')
    operator = fields.Many2one(comodel_name='hr.employee', string='Operator')
    objectives_for_requesting_job = fields.Char(
        string='As the Engineer-In-Charge, I understand that the Client’s objectives for requesting this job are:')

    certifications_line_ids = fields.One2many(
        comodel_name='job.call.out.form.certifications', inverse_name='job_call_out_form_id')

    responsible_for_safety = fields.Many2one(
        comodel_name='hr.employee', string='The person responsible for Safety on the job (and possesses HSE Level 3 Certification) is')
    have_hse3 = fields.Selection([('1', 'Yes'), ('2', 'No')],
                                 string='HSE Level 3? ', track_visibility='onchange')

    engineer_in_charge_approval = fields.Many2one(
        'res.users', 'Engineer-In-Charge Signature:', readonly=True, track_visibility='onchange')
    engineer_in_charge_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    @api.multi
    def button_engineer_in_charge_sign(self):
        self.engineer_in_charge_approval_date = date.today()
        self.engineer_in_charge_approval = self._uid


class JobCallOutFormCertifications(models.Model):
    _name = "job.call.out.form.certifications"
    _description = 'Job Call Out Form'

    job_call_out_form_id = fields.Many2one(comodel_name='job.call.out.form')

    cert_work = fields.Char(string='Certification/Work Experience')
    crew_member = fields.Many2one(
        comodel_name='hr.employee', string='Crew Members that hold it')


class Project(models.Model):
    _name = "project.project"
    _inherit = ['project.project', 'mail.thread',
                'mail.activity.mixin', 'rating.mixin']
    _description = "Project"

    _sql_constraints = [
        ('project_code_uniq', 'UNIQUE(project_code)', 'Project Code must be Unique')]

    crm_lead_id = fields.Many2one(comodel_name='crm.lead', string='Lead')

    project_code = fields.Char('Project Code', readonly=True,
                               required=True, index=True, copy=False, default='New')

    site_eng_id = fields.Many2one(
        comodel_name="hr.employee", string="Site Engineer", required=False, )
    project_team_ids = fields.Many2many(
        comodel_name="hr.employee", string="Project Team", )

    @api.model
    def create(self, vals):
        if vals.get('project_code', 'New') == 'New':
            vals['project_code'] = self.env['ir.sequence'].next_by_code(
                'project.code') or '/'
        return super(Project, self).create(vals)


class Lead(models.Model):
    _name = "crm.lead"
    _inherit = 'crm.lead'

    bid_category = fields.Selection([('technical', 'Technical Bid'), (
        'commercial', 'Commercial Bid')], string='Bid Category', required=False)

    contract_start_date = fields.Date(string='Start Date')
    contract_end_date = fields.Date(string='End Date')
    document_submission_date = fields.Date(string='Document Submission Date')

    @api.multi
    def write(self, vals):
        if vals.get('stage_id.name', 'Negotiation') == 'Negotiation':
            group_id = self.env['ir.model.data'].xmlid_to_object(
                'account.group_account_manager')
            user_ids = []
            partner_ids = []
            for user in group_id.users:
                user_ids.append(user.id)
                partner_ids.append(user.partner_id.id)
            self.message_subscribe(partner_ids=partner_ids)
            subject = "Budget report is needed for this oppurtunity '{}' ".format(
                self.name)
            self.message_post(subject=subject, body=subject,
                              partner_ids=partner_ids)
        return super(Lead, self).write(vals)


class MaintenanceRequest(models.Model):
    _name = 'maintenance.request'
    _inherit = 'maintenance.request'
    _order = "create_date desc"

    maintenance_type = fields.Selection([('corrective', 'Corrective'), ('preventive', 'Preventive'), (
        'breakdown', 'Breakdown')], string='Maintenance Type', default="corrective")
    asset_number = fields.Char('Asset Number')

    seq_name = fields.Char('Order Reference', readonly=True,
                           required=True, index=True, copy=False, default='New')
    active = fields.Boolean(string="Active", default=True)

    @api.model
    def create(self, vals):
        if vals.get('seq_name', 'New') == 'New':
            vals['seq_name'] = self.env['ir.sequence'].next_by_code(
                'maintenance.request') or '/'
        return super(MaintenanceRequest, self).create(vals)

    @api.multi
    def unlink(self):
        for request in self:
            if request.stage_id != self._default_stage():
                raise UserError(
                    "You can only delete requests in %s stage!!!" % self._default_stage().name)
            return super(MaintenanceRequest, self).unlink()

    @api.multi
    def button_submit_maintenance_manager(self):
        self.stage_id = 5
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Maintenance Request '{}' has been submitted, awaiting your approval".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_submit_qaqc(self):
        self.stage_id = 6
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'quality.group_quality_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Maintenance Request '{}' is awaiting your approval".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_submit_store(self):
        self.stage_id = 7
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'stock.group_stock_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Maintenance Request '{}' has been created, awaiting your approval".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_approval_maintenance_manager(self):
        subject = "Maintenance Request {} has been approved by Maintenance Manager".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_qaqc()

    @api.multi
    def button_approval_qaqc_manager(self):
        subject = "Maintenance Request {} has been approved by QA/QC Manager".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_store()

    @api.multi
    def button_approval_store_manager(self):
        self.stage_id = 2
        subject = "Maintenance Request {} has been approved by Store Manager".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_repair(self):
        self.stage_id = 3
        subject = "Maintenance Request {} has been Rejected".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_scrap(self):
        self.stage_id = 4
        subject = "Maintenance Request {} has been Scrapped".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_reject(self):
        self.stage_id = 8
        subject = "Maintenance Request {} has been Rejected".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit = 'fleet.vehicle'

    def _default_department(
            self):  # this method is to search the hr.employee and return the department id of the person clicking the form atm
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    def _default_employee(
            self):  # this method is to search the hr.employee and return the user id of the person clicking the form atm
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee Name:', default=_default_employee)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', default=_default_department)
    acquisition_date = fields.Date('Registration Date', required=False,
                                   default=fields.Date.today, help='Date when the vehicle has been Registered')
    asset_number = fields.Char(string='Asset Number')
    project_id = fields.Many2one(
        comodel_name='project.project', string='Project')
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    duration = fields.Char(string='Duration')


class FleetVehicleCost(models.Model):
    _name = 'fleet.vehicle.cost'
    _inherit = 'fleet.vehicle.cost'

    vehicle_return_date = fields.Date(string='Return Date')
    vehicle_date_of_standby = fields.Date(string='Date of Standby')
    reason_for_standby = fields.Char(
        string='Reason for standby', help="reason for delay. When return date is due and vehicle is yet to be returned")


class Task(models.Model):
    _inherit = "project.task"

    task_done = fields.Boolean(string='task Completed', copy=False)
    task_team_ids = fields.Many2many(comodel_name='hr.employee', string='Team')

    @api.depends('effective_hours', 'subtask_effective_hours', 'planned_hours')
    def _compute_progress_hours(self):
        for task in self:
            if (task.planned_hours > 0.0):
                task_total_hours = task.effective_hours + task.subtask_effective_hours
                if task_total_hours > task.planned_hours and task.remaining_hours > 0:
                    task.progress = 100
                elif task.remaining_hours < 0:
                    task.progress = 80
                else:
                    task.progress = round(
                        100.0 * task_total_hours / task.planned_hours, 2)

    @api.onchange('progress')
    def _onchange_progress(self):
        if self.remaining_hours < 0:
            self.progress = 80

    @api.multi
    def button_task_complete(self):
        if any(task for task in self.timesheet_ids):
            self.progress = 100
            self.task_done = True
            # self.stage_id.name = "DONE"
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Go, go, go! Congrats on your task completion.',
                    'img_url': '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            warning_mess = {
                'title': _('No Task(s) Recorded!'),
                'message': _("You have attempted to mark a task as done without any timesheet lines "
                             "please do specify some timesheet line(s)."),
            }
            user_warning = _(
                'You have attempted to mark a task as done without any timesheet recording(s), please do specify some timesheet line(s).')
            # return {'warning': warning_mess}
            raise UserError(user_warning)


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    start_time = fields.Float(string='Start Time', required=True)
    start_time_am_pm = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')], string='AM/PM', copy=False)

    end_time = fields.Float(string='End Time', required=True)
    end_time_am_pm = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')], string='AM/PM', copy=False)


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ['sale.order']
    _description = "Quotation"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('gm', 'GM Approval'),
        ('md', 'MD Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    @api.multi
    def button_submit(self):
        self.write({'state': 'gm'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_gm')
        user_ids = []
        partner_ids = []
        # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
        for user in group_id.users:
            user_ids.append(user.id)
            # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Service Order '{}' needs approval from GM".format(self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_submit_to_md(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_md')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Quotation '{}' needs approval from MD".format(self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def action_gm_approval(self):
        self.write({'state': 'md'})
        subject = "Quotation {} has been approved by GM".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_to_md()


class HolidaysRequest(models.Model):
    _name = "hr.leave"
    _inherit = "hr.leave"

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
        help="The status is set to 'To Submit', when a leave request is created." +
        "\nThe status is 'To Approve', when leave request is confirmed by user." +
        "\nThe status is 'Refused', when leave request is refused by manager." +
        "\nThe status is 'Approved', when leave request is approved by manager.")


class HolidaysType(models.Model):
    _name = "hr.leave.type"
    _inherit = "hr.leave.type"

    # TODO: remove me in master
    def _inverse_validation_type(self):
        for holiday_type in self:
            if holiday_type.double_validation == True:
                holiday_type.validation_type = 'both'
            else:
                # IF to preserve the information (hr or manager)
                if holiday_type.validation_type == 'both':
                    holiday_type.validation_type = 'manager'


class MaintenanceEquipment(models.Model):
    _name = 'maintenance.equipment'
    _inherit = "maintenance.equipment"

    # this method is to search the hr.employee and return the department id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', default=_default_department)
    asset_number = fields.Char('Asset Number')
    current_status = fields.Char(string='Current Status')


class VendorAudit(models.Model):
    _name = "vendor.audit.form"
    _description = 'Vendor Audit Form'
    _rec_name = 'vendor_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vendor_id = fields.Many2one(comodel_name="res.partner", )
    reg_date = fields.Date(string="Date", required=False,
                           default=fields.Date.context_today)
    visited_by = fields.Many2one(comodel_name='hr.employee', required=False, )
    cat_of_supply = fields.Char(string="Category of Supply", required=False, )
    contact_person = fields.Char(string="Contact Person", required=False, )
    hse = fields.Many2one('hr.employee', string='HSE')

    management_vendor_audit_ids = fields.One2many(
        comodel_name="management.vendor.audit", inverse_name="vendor_audit_id", string="Management Responsibilty", copy=True, )
    fundamentals_vendor_audit_ids = fields.One2many(
        comodel_name="fundamentals.vendor.audit", inverse_name="vendor_audit_id", string="Fundamentals", copy=True)
    competency_vendor_audit_ids = fields.One2many(
        comodel_name="competency.vendor.audit", inverse_name="vendor_audit_id", string="Competency", copy=True)
    quality_vendor_audit_ids = fields.One2many(
        comodel_name="quality.vendor.audit", inverse_name="vendor_audit_id", string="Quality Systems", copy=True)

    audit_score = fields.Integer(string="Audit Score", required=False, )
    is_required = fields.Boolean(string="Follow-up required",)
    details = fields.Text(string="If yes, provide details:", required=False, )

    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'),
                                                         ('validate',
                                                          'Validate'), ('refuse', 'Refuse'),
                                                         ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'

    # Smart Button
    @api.multi
    def hse_vendor_audit_checklist(self):
        return {
            'name': _('HSE Requirements'),
            'domain': [('vendor_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'hse.vendor.audit.checklist',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }


class ManagementVendorAudit(models.Model):
    _name = "management.vendor.audit"
    _description = 'Management Responsibilty Vendor Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vendor_audit_id = fields.Many2one(
        comodel_name="vendor.audit.form", string="Management Responsibilty", required=False, )

    checklist = fields.Selection(string="Section", selection=[(
        '1.1', 'Management Commitment and Review')], required=False, )

    mark = fields.Selection(string="Mark", selection=[('fully', 'Fully Meets'), ('partial', 'Partially Meets'),
                                                      ('not', 'Does Not Meet'), ('failure',
                                                                                 'Critical Failure'),
                                                      ('not_applicable', 'Not Applicable')], required=False, )


class FundamentalsVendorAudit(models.Model):
    _name = "fundamentals.vendor.audit"
    _description = 'Fundamentals Responsibilty Vendor Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vendor_audit_id = fields.Many2one(
        comodel_name="vendor.audit.form", string="Fundamentals Responsibilty", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('2.1', 'Infrastructure'), ('2.2', 'Training & Education'),
                                                           ('2.3', 'Handling, Storage & Delivery'), (
                                                               '2.4', 'Control of Materials'),
                                                           ('2.5', 'Traceability and Crisis Management'), (
                                                               '2.6', 'Calibration, Measuring and Test Equipment'),
                                                           ('2.7', 'Maintenance')], required=False, )

    mark = fields.Selection(string="Mark", selection=[('fully', 'Fully Meets'), ('partial', 'Partially Meets'),
                                                      ('not', 'Does Not Meet'), ('failure',
                                                                                 'Critical Failure'),
                                                      ('not_applicable', 'Not Applicable')], required=False, )


class CompetencyVendorAudit(models.Model):
    _name = "competency.vendor.audit"
    _description = 'Competency Responsibilty Vendor Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vendor_audit_id = fields.Many2one(
        comodel_name="vendor.audit.form", string="Competency Responsibilty", required=False, )

    mark = fields.Selection(string="Mark", selection=[('fully', 'Fully Meets'), ('partial', 'Partially Meets'),
                                                      ('not', 'Does Not Meet'), ('failure',
                                                                                 'Critical Failure'),
                                                      ('not_applicable', 'Not Applicable')], required=False, )
    checklist = fields.Selection(string="ITEM", selection=[('3.1', 'Company registration requirements (CAC, TIN, DPR, Local Content)'), ('3.2', 'Financial capacity/stability'),
                                                           ('3.3', 'Evidence of existing customer list'), ('3.4', 'Foreign procurement measures')], required=False, )


class QualityVendorAudit(models.Model):
    _name = "quality.vendor.audit"
    _description = 'Quality Systems Vendor Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vendor_audit_id = fields.Many2one(
        comodel_name="vendor.audit.form", string="Quality Responsibilty", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('4.1', 'Confomance to customer specifications'), ('4.2', 'Quality Standard'),
                                                           ('4.3', 'ISO Certifications'), ('4.4',
                                                                                           'Document COntrol & Record Keeping'),
                                                           ('4.5', 'Corrective & Preventive Action for non-conformity'),
                                                           ('4.6', 'Customer Service')], required=False, )

    mark = fields.Selection(string="Mark", selection=[('fully', 'Fully Meets'), ('partial', 'Partially Meets'),
                                                      ('not', 'Does Not Meet'), ('failure',
                                                                                 'Critical Failure'),
                                                      ('not_applicable', 'Not Applicable')], required=False, )


class HseVendorAuditChecklist(models.Model):
    _name = "hse.vendor.audit.checklist"
    # _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HSE Requirements for Vendor'

    vendor_id = fields.Many2one(comodel_name="res.partner", required=False, )

    sustainability_hse_vendor_audit_checklist_ids = fields.One2many(
        comodel_name="sustainability.hse.vendor.audit.checklist", inverse_name="hse_vendor_audit_id", string="Management Responsibilty", copy=True, )
    structure_hse_vendor_audit_checklist_ids = fields.One2many(
        comodel_name="structure.hse.vendor.audit.checklist", inverse_name="hse_vendor_audit_id", string="Fundamentals", copy=True)
    environmental_hse_vendor_audit_checklist_ids = fields.One2many(
        comodel_name="environmental.hse.vendor.audit.checklist", inverse_name="hse_vendor_audit_id", string="Competency", copy=True)
    social_hse_vendor_audit_checklist_ids = fields.One2many(
        comodel_name="social.hse.vendor.audit.checklist", inverse_name="hse_vendor_audit_id", string="Quality Systems", copy=True)

    risk_score = fields.Selection(string="Overall Sustainability Risk Score", selection=[('high', 'Urgently needs Improvement High Risk'),
                                                                                         ('increased', 'To be Improved Increased risk'),
                                                                                         ('medium', 'Needs Attention Medium risk'),
                                                                                         ('slight', 'Acceptable Slight risk'),
                                                                                         ('low', 'Good Low Risk')], required=False, )


class SustainabilityHseVendorAuditChecklist(models.Model):
    _name = "sustainability.hse.vendor.audit.checklist"
    _description = 'Quality Systems Vendor Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hse_vendor_audit_id = fields.Many2one(
        comodel_name="hse.vendor.audit.checklist", string="Sustainability Risk Score", required=False, )

    section = fields.Selection(string="Sustainability Risk Score", selection=[('1.0', 'Company structure/organization/response'),
                                                                              ('2.0', 'Location and environmental impact'),
                                                                              ('3.0', 'Employee safety ad health')], required=False, )

    check = fields.Selection(string="Check", selection=[('score_1', 'Urgently needs Improvement High Risk'),
                                                        ('score_2',
                                                         'To be Improved Icreased risk'),
                                                        ('score_3',
                                                         'Needs Attention Medium risk'),
                                                        ('score_4',
                                                         'Acceptable Slight risk'),
                                                        ('score_5', 'Good Low Risk')], required=False, )


class StructureHseVendorAuditChecklist(models.Model):
    _name = "structure.hse.vendor.audit.checklist"
    _description = 'Quality Systems Vendor Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hse_vendor_audit_id = fields.Many2one(
        comodel_name="hse.vendor.audit.checklist", string="Company structure/organization/response", required=False, )

    section = fields.Selection(string="Company structure/organization/response", selection=[('1.1', 'The Company has clear HSE policy in place that has been signed by the senior manager'),
                                                                                            ('2.1', 'There is clear awateness of hazards on site and their potential impact on society, the environment and people if not well controlled'),
                                                                                            ('3.1', 'Has emergency equipment been installed at site in relation to the hazards present e.g Fire Extinguisher, First Aid Box')], required=False, )
    check = fields.Selection(string="Check", selection=[(
        'no', 'NO'), ('yes', 'YES'), ], required=False, )
    remark = fields.Char(string="Evidence/ Remarks", required=False, )


class EnvironmentalHseVendorAuditChecklist(models.Model):
    _name = "environmental.hse.vendor.audit.checklist"
    _description = 'Quality Systems Vendor Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hse_vendor_audit_id = fields.Many2one(comodel_name="hse.vendor.audit.checklist",
                                          string="Environmental dimension: Location and environment impact", required=False, )

    section = fields.Selection(string="Environmental dimension: Location and environment impact", selection=[('1.2', 'Irregular or regular frequent inspection visits from governmental or local authorities take place'),
                                                                                                             ('2.2', 'The company provides waste containment for waste disposal')], required=False, )
    check = fields.Selection(string="Check", selection=[(
        'no', 'NO'), ('yes', 'YES'), ], required=False, )
    remark = fields.Char(string="Evidence/ Remarks", required=False, )


class SocialHseVendorAuditChecklist(models.Model):
    _name = "social.hse.vendor.audit.checklist"
    _description = 'Quality Systems Vendor Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hse_vendor_audit_id = fields.Many2one(comodel_name="hse.vendor.audit.checklist",
                                          string="Social dimension: Employee safety and health", required=False, )

    section = fields.Selection(string="Social dimension: Employee safety and health", selection=[('1.3', 'Company ensures that no child labor (<16 yrs; <18 yrs for hazardous work) or forced labor are used'),
                                                                                                 ('2.3', 'Safety & Health information has been easily made available for the employees, Eg Safety procedures of their activities, Use of PPEs etc'),
                                                                                                 ('3.3', 'Access for employees to safe potable water, hygenic toilettes, sanitary facilities and eating facilities, ventilation has been provided by the company')], required=False, )
    check = fields.Selection(string="Check", selection=[(
        'no', 'NO'), ('yes', 'YES'), ], required=False, )
    remark = fields.Char(string="Evidence/ Remarks", required=False, )

    note = fields.Text(string="Remarks", required=False, )


class VehiclePretripChecklist(models.Model):
    _name = "vehicle.pretrip.checklist"
    _description = 'Vehicle Pre- trip Inspection Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle', string='Vehicle Name')

    interior_vehicle_checklist_ids = fields.One2many(
        comodel_name='interior.vehicle.checklist', inverse_name='vehicle_pretrip_checklist_id', string="Interior", copy=True)
    indicator_vehicle_checklist_ids = fields.One2many(
        comodel_name='indicator.vehicle.checklist', inverse_name='vehicle_pretrip_checklist_id', string="Indicator", copy=True)
    lights_vehicle_checklist_ids = fields.One2many(
        comodel_name='lights.vehicle.checklist', inverse_name='vehicle_pretrip_checklist_id', string="Lights", copy=True)
    mirrors_vehicles_checklist_ids = fields.One2many(
        comodel_name='mirrors.vehicle.checklist', inverse_name='vehicle_pretrip_checklist_id', string="Mirrors", copy=True)
    particulars_vehicle_checklist_ids = fields.One2many(
        comodel_name="particulars.vehicle.checklist", inverse_name="vehicle_pretrip_checklist_id", string="Particulars", required=False, copy=True, )
    accessories_vehicle_checklist_ids = fields.One2many(
        comodel_name="accessories.vehicle.checklist", inverse_name="vehicle_pretrip_checklist_id", string="Accessories", required=False, copy=True, )
    engine_vehicle_checklist_ids = fields.One2many(
        comodel_name="engine.vehicle.checklist", inverse_name="vehicle_pretrip_checklist_id", string="Engine Check", required=False, copy=True, )
    exterior_vehicle_checklist_ids = fields.One2many(
        comodel_name="exterior.vehicle.checklist", inverse_name="vehicle_pretrip_checklist_id", string="Exterior", required=False, copy=True, )
    additional_vehicle_checklist_ids = fields.One2many(
        comodel_name="additional.vehicle.checklist", inverse_name="vehicle_pretrip_checklist_id", string="Additioanl Checks", required=False, copy=True, )

    checker = fields.Many2one('hr.employee', 'Checker',
                              track_visibility='onchange')
    approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    journey_manager = fields.Many2one(
        'hr.employee', 'Journey Manager', track_visibility='onchange')
    driver = fields.Many2one('hr.employee', 'Driver',
                             track_visibility='onchange')
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('refuse', 'Refuse'),
                                                         ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'
        if self.state == "approved":
            self.approval_date = date.today()


class InteriorVehicleChecklist(models.Model):
    _name = 'interior.vehicle.checklist'
    # _rec_name = 'vehicle_id'
    _description = 'Vehicle Interior Pre- trip Inspection Checklist'

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="Interior", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('seats', 'Seats & head rest'), ('seat_belt', 'Seat belts ok and clean'),
                                                           ('wwwf', 'Windscreen wiper, washer, fluid'), (
                                                               'floor', 'Floor mat secured, pedals free'),
                                                           ('horn', 'Horn'), ('radio',
                                                                              'Radio'),
                                                           ('pedal', 'Pedal and Hand Brakes'), (
                                                               'doors', 'Doors, Door window and locks'),
                                                           ('air-conditioner', 'Air conditioner, Heater'), (
                                                               'communication', 'Communication Radio/GSM'),
                                                           ('alarm', 'Reverse Alarm'), ('ivms', 'IVMS/ASTRATA')], required=False, )

    status = fields.Selection(string="Status", selection=[(
        'ok', 'OK'), ('not_ok', 'NOT OK'), ], required=False, )
    # ok = fields.Boolean(string='OK')
    # not_ok = fields.Boolean(string='NOT OK')
    remark = fields.Char(string='Remark/Comment')


class IndicatorVehicleChecklist(models.Model):
    _name = "indicator.vehicle.checklist"
    _description = 'Indicator Pre- Trip Vehicle Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="Indicator", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('guage', 'Fuel Gauge'), ('fuel', 'Fuel Level'),
                                                           ('temp', 'Temperature'), (
                                                               'speedometer', 'Speedometer'),
                                                           ('warning', 'No warning signal on dash board')], required=False, )

    status = fields.Selection(string="Status", selection=[(
        'ok', 'OK'), ('not_ok', 'NOT OK'), ], required=False, )
    remark = fields.Char(string='Remark/Comment')


class LightsVehicleChecklist(models.Model):
    _name = "lights.vehicle.checklist"
    _description = 'lights Pre- Trip Vehicle Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="lights", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('parking', 'Parking Light'), ('side', 'Side Light'),
                                                           ('brake', 'Brake Light'), ('fog',
                                                                                      'Fog Lights'),
                                                           ('hazard', 'Hazard warning Lights'), (
                                                               'headlights', 'Headlights'),
                                                           ('trafficator', 'Trafficator'), ('reverse', 'Reverse and Beacon Light')], required=False, )
    status = fields.Selection(string="Status", selection=[(
        'ok', 'OK'), ('not_ok', 'NOT OK'), ], required=False, )
    remark = fields.Char(string='Remark/Comment')


class MirrorsVehicleChecklist(models.Model):
    _name = "mirrors.vehicle.checklist"
    _description = 'mirrors Pre- Trip Vehicle Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="mirrors", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('side', 'Side mirrors'), ('inner', 'Inner mirrors'),
                                                           ('obstruction', 'No obstruction under or around')], required=False, )
    status = fields.Selection(string="Status", selection=[(
        'ok', 'OK'), ('not_ok', 'NOT OK'), ], required=False, )
    remark = fields.Char(string='Remark/Comment')


class ParticularsVehicleChecklist(models.Model):
    _name = "particulars.vehicle.checklist"
    _description = 'particulars Pre- Trip Vehicle Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="particulars", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('licence', 'Vehicle licence and Permits'), ('insurance', 'Insurance'),
                                                           ('premob', 'Current Premob Certificate'), (
                                                               'd_lincence', 'Drivers Driving licence'),
                                                           ('log_book', 'Log Book')], required=False, )
    status = fields.Selection(string="Status", selection=[(
        'ok', 'OK'), ('not_ok', 'NOT OK'), ], required=False, )
    remark = fields.Char(string='Remark/Comment')


class AccessoriesVehicleChecklist(models.Model):
    _name = "accessories.vehicle.checklist"
    _description = 'accessories Pre- Trip Vehicle Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="accessories", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('tyre', 'Spare Tyre'), ('jack', 'Jack'),
                                                           ('w_spanner', 'Wheel Spanner'), (
                                                               'plate', 'Number plate (Front and Rear)'),
                                                           ('fire', 'Fire Extinguisher'), (
                                                               'reflector', 'Triangular Reflector'),
                                                           ('first_aid', 'First Aid Box')], required=False, )
    status = fields.Selection(string="Status", selection=[(
        'ok', 'OK'), ('not_ok', 'NOT OK'), ], required=False, )
    remark = fields.Char(string='Remark/Comment')


class EngineVehicleChecklist(models.Model):
    _name = "engine.vehicle.checklist"
    _description = 'engine Pre- Trip Vehicle Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="engine", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('brake', 'Brake fluid level'), ('engine', 'Engine oil level'),
                                                           ('radiator', 'Radiator fluid level'), (
                                                               'transmission', 'Transmission (P/Steering) fluid'),
                                                           ('e_sound', 'Engine Sound'), (
                                                               'battery', 'Battery Terminal/Clamp'),
                                                           ('wire', 'No loose or naked wore'), (
                                                               'fan', 'Fan blade, belts and pulleys ok'),
                                                           ('exhaust', 'Exhaust condition'), ('spark', 'Spark Arrestor')], required=False, )
    status = fields.Selection(string="Status", selection=[(
        'ok', 'OK'), ('not_ok', 'NOT OK'), ], required=False, )
    remark = fields.Char(string='Remark/Comment')


class ExteriorVehicleChecklist(models.Model):
    _name = "exterior.vehicle.checklist"
    _description = 'exterior Pre- Trip Vehicle Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="exterior", required=False, )

    checklist = fields.Selection(string="ITEM", selection=[('tyres', 'Tyres and air pressure'), ('t_condition', 'Tyres condition and thread level'),
                                                           ('wheel', 'Wheel cover (Present)'), (
                                                               'rims', 'Rims, nuts and shock absorber'),
                                                           ('body', 'Body condition'), ('hammers',
                                                                                        '**Emergency exit hammers'),
                                                           ('kit', '**Accident kit (reflector shirt, flashlight)')], required=False, )
    status = fields.Selection(string="Status", selection=[(
        'ok', 'OK'), ('not_ok', 'NOT OK'), ], required=False, )
    remark = fields.Char(string='Remark/Comment')


class AdditionalVehicleChecklist(models.Model):
    _name = "additional.vehicle.checklist"
    _description = 'Additional Vehicle Checks'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_pretrip_checklist_id = fields.Many2one(
        comodel_name="vehicle.pretrip.checklist", string="Additional Checks", required=False, )

    checklist = fields.Selection(string="For Medium/Heavy fleet", selection=[('reflector', 'Rear reflector'), ('load', 'Load ok and secured'), ('manifest', 'Manifest'),
                                                                             ('outriggers', 'Outriggers'), (
                                                                                 'legs', 'Landing legs and hooks'),
                                                                             ('spray', 'Spray suppression (mud flaps)'), (
                                                                                 'ladder', 'ladder/steps'), ('guard', 'Under-run guard'),
                                                                             ('pump', 'pump and meter'), (
                                                                                 'crane', 'Crane/lifting tackle'), ('mast', 'Mast/chain'),
                                                                             ('forks', 'forks'), ('hook', 'hook block'), ('tailgate', 'tailgate ramp')], required=False, )
    ok = fields.Boolean(string='OK')


class LogisticsVendorAuditChecklist(models.Model):
    _name = 'logistics.vendor.audit.checklist'
    _rec_name = 'vendor_id'
    _description = 'Logistics Vendor Audit Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vendor_id = fields.Many2one(comodel_name="res.partner", required=True, )

    has_cac = fields.Boolean(string="Have CAC documents been provided",)
    has_tax = fields.Boolean(
        string="Has current income TAX clearance certificate been provided",)
    has_pre_mob = fields.Boolean(
        string="Has pre-mob certificate of equipment been provided",)
    has_comp = fields.Boolean(
        string="Has current workmen compensation insurance/third party liability been provided",)
    has_mou = fields.Boolean(
        string="Has MOU/evidence of equipment ownership been provided",)
    has_competence = fields.Boolean(
        string="Has evidence of Operator/Employee competence been provided",)
    has_road_req = fields.Boolean(
        string="Is there a valid evidence of Road Statutory Requirement Compliance",)

    has_logistics = fields.Boolean(
        string="Is there an approved Logistics Management Procedure",)
    has_maintenance = fields.Boolean(
        string="Is there an approved Preventive Maintenance Program",)
    has_equipment = fields.Boolean(
        string="Is there an approved Equipment Operating Procedure",)

    has_necessary = fields.Boolean(
        string="Are the necessary equipment equipped with loading, offloading apparatus (e.g belts, slings, chains etc)",)
    is_certified = fields.Boolean(
        string="Are the necessary equipment certified fit for use",)
    was_sighted = fields.Boolean(
        string="Were the required equipment physically sighted",)
    has_safety = fields.Boolean(
        string="Are safety apparatus provided for the Operator/employee",)

    is_accepted = fields.Boolean(string="Accepted",)
    remarks = fields.Text(string="Comment", required=False, )

    audited_by_id = fields.Many2one(
        comodel_name="hr.employee", string="Audited by", required=False, )
    date = fields.Date(string="Date", required=False,
                       default=fields.Date.context_today)
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('refuse', 'Refuse'),
                                                         ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'


class SupplierEvalForm(models.Model):
    _name = 'supplier.evaluation.form'
    _rec_name = 'supplier_id'
    _description = 'Supplier Evaluation Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    supplier_id = fields.Many2one(comodel_name="res.partner", required=True, )
    supply_scope = fields.Char(string="Scope of Supply", required=False, )
    company_rep = fields.Char(string="Company Representative",)
    email = fields.Char(string="Email", required=False, )
    job_title = fields.Char(string="Job Title", required=False, )
    phone = fields.Integer(string="Tel. No", required=False, )
    eval_date = fields.Date(string="Date", required=False,
                            default=fields.Date.context_today)

    question_1 = fields.Integer(
        string="How long have you been in the business?", required=False, )
    reg_evidence = fields.Binary(
        string="Attach Evidence of Registration/Operation",)
    question_2 = fields.Text(
        string="Give details of other companies utilizing your product/service", required=False, )
    sales_type = fields.Selection(string="Sales Type", selection=[(
        'cash', 'Cash'), ('credit', 'Credit'), ], required=False, )
    credit_duration = fields.Integer(string="Credit Days", required=False, )
    # acceptance_criteria_ids = fields.One2many(comodel_name="supplier.eval.acceptance.criteria", inverse_name="", string="", required=False, )

    has_track_record = fields.Boolean(string="Track Records",)
    has_facility_audit = fields.Boolean(string="Facility Audit",)
    is_recommended = fields.Boolean(string="Recommeded by Client",)
    has_sole_source = fields.Boolean(string="Sole Source",)
    is_accepted = fields.Boolean(string="Accepted",)
    comments = fields.Text(string="Comments", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('refuse', 'Refuse'),
                                                         ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'


class SupplierRevaluation(models.Model):
    _name = 'supplier.revaluation'
    _rec_name = 'supplier_id'
    _description = 'SUPPLIER RE-EVALUATION'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    supplier_id = fields.Many2one(comodel_name='res.partner', required=True, )
    scope = fields.Char(string="Scope of Supply", required=False, )
    supplier_revaluation_ids = fields.One2many(
        "supplier.revaluation.lines", "supplier_revaluation_id", string="RE-EVALUATION CRITERIA", required=False, )

    mark = fields.Selection(string="Mark", selection=[(
        'accept', 'Acceptable'), ('not', 'Do not use'), ], required=False, )
    efficency_score = fields.Integer(string="Efficiency =", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('refuse', 'Refuse'),
                                                         ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'


class SupplierRevaluationLines(models.Model):
    _name = 'supplier.revaluation.lines'

    supplier_revaluation_id = fields.Many2one(
        comodel_name="supplier.revaluation", string="RE-EVALUATION CRITERIA", required=False, )
    criteria = fields.Selection(string="RE-EVALUATION CRITERIA", selection=[('1', 'Quality of past delivery'),
                                                                            ('2', 'Delivery time'),
                                                                            ('3', 'Service provision (response, communication)')], required=False, )

    score_1 = fields.Float(
        string="1- PROCUREMENT ASSESSMENT VALUE",  required=False, )
    score_2 = fields.Float(
        string="2 - QA/QC ASSESSMENT VALUE",  required=False, )
    score_3 = fields.Float(
        string="3 - INDICATOR WEIGHING FACTOR",  required=False, )
    score_4 = fields.Float(
        string="4 - PERFORMANCE INDICATOR (1+2) X 3 =%",  required=False, )


class CathodicProtectionEquipmentList(models.Model):
    _name = 'cathodic.protection.checklist'
    _rec_name = 'project_id'
    _description = 'Cathodic Protection Equipment Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one(
        comodel_name='project.project', string='Project Name', required=True, )
    cathodic_protection_checklist_ids = fields.One2many(comodel_name="cathodic.protection.checklist.lines",
                                                        inverse_name="cathodic_protection_checklist_id", string="Equipment Checklist", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Validate'),
                                                         ('refuse', 'Refuse'), ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def validate_request(self):
        self.state = 'validate'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'


class CathodicProtectionEquipmentLines(models.Model):
    _name = 'cathodic.protection.checklist.lines'
    _description = 'Cathodic Protection Equipment Checklist Lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one(
        comodel_name="product.template", string="Item", required=False, )
    description = fields.Char(string="Description", required=False, )
    qty_mob = fields.Float(string="QTY MOB",  required=False, )
    qty_demo = fields.Float(string="QTY DEMO B",  required=False, )
    remarks = fields.Char(string="De-MOB Remarks", required=False, )
    cathodic_protection_checklist_id = fields.Many2one(
        comodel_name="cathodic.protection.checklist", string="Equipment Checklist", required=False, )


class ValvesServiceChecklist(models.Model):
    _name = 'valves.service.checklist'
    _rec_name = 'project_id'
    _description = 'Valves Service Equipment Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    staff_id = fields.Many2one(
        comodel_name="hr.employee", string="Name", required=False, )
    date = fields.Date(string="Date", required=False,
                       default=fields.Date.context_today)
    project_id = fields.Many2one(
        comodel_name='project.project', string='Project Name', required=True, )
    valves_service_checklist_ids = fields.One2many(comodel_name="valves.service.checklist.lines",
                                                   inverse_name="values_service_checklist_id", string="Valves Service", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Validate'),
                                                         ('refuse', 'Refuse'), ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def validate_request(self):
        self.state = 'validate'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'


class ValvesServiceChecklistLines(models.Model):
    _name = 'valves.service.checklist.lines'
    _description = 'Valves Service Checklist Lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one(
        comodel_name="product.template", string="Item", required=False, )
    description = fields.Char(string="Description", required=False, )
    qty_mob = fields.Float(string="QTY MOB",  required=False, )
    qty_demo = fields.Float(string="QTY DEMO B",  required=False, )
    remarks = fields.Char(string="De-MOB Remarks", required=False, )
    values_service_checklist_id = fields.Many2one(
        comodel_name="valves.service.checklist", string="Valves Service Checklist", required=False, )


class PumpEquipmentChecklist(models.Model):
    _name = 'pump.equipment.checklist'
    _rec_name = 'staff_id'
    _description = 'Pump Equipment Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    staff_id = fields.Many2one(
        comodel_name="hr.employee", string="Name", required=False, )
    location = fields.Char(string="Location", required=False, )
    job = fields.Char(string="job", required=False, )
    pump_checklist_ids = fields.One2many(comodel_name="pump.equipment.checklist.lines",
                                         inverse_name="pump_checklist_id", string="Valves Service", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Validate'),
                                                         ('refuse', 'Refuse'), ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def validate_request(self):
        self.state = 'validate'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'


class PumpEquipmentChecklistLines(models.Model):
    _name = 'pump.equipment.checklist.lines'
    _description = 'Pump Equipment Checklist Lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one(
        comodel_name="product.template", string="Item", required=False, )
    description = fields.Char(string="Description", required=False, )
    qty_mob = fields.Float(string="QTY MOB",  required=False, )
    qty_demo = fields.Float(string="QTY DEMO B",  required=False, )
    remarks = fields.Char(string="De-MOB Remarks", required=False, )
    pump_checklist_id = fields.Many2one(
        comodel_name="pump.equipment.checklist", string="Pump Equipment Checklist", required=False, )


class PiggingEquipmentChecklist(models.Model):
    _name = 'pigging.equipment.checklist'
    _rec_name = 'staff_id'
    _description = 'Pigging Equipment Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    staff_id = fields.Many2one(
        comodel_name="hr.employee", string="Name", required=False, )
    date = fields.Date(string="Date", required=False,
                       default=fields.Date.context_today)
    project_id = fields.Many2one(
        comodel_name='project.project', string='Project Name', required=True, )
    pigging_checklist_ids = fields.One2many(comodel_name="pigging.equipment.checklist.lines",
                                            inverse_name="pigging_checklist_id", string="Pigging Equipment", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Validate'),
                                                         ('refuse', 'Refuse'), ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def validate_request(self):
        self.state = 'validate'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'


class PiggingEquipmentChecklistLines(models.Model):
    _name = 'pigging.equipment.checklist.lines'
    _description = 'Pigging Equipment Checklist Lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one(
        comodel_name="product.template", string="Item", required=False, )
    description = fields.Char(string="Description", required=False, )
    qty_mob = fields.Float(string="QTY MOB",  required=False, )
    qty_demo = fields.Float(string="QTY DEMO B",  required=False, )
    remarks = fields.Char(string="De-MOB Remarks", required=False, )
    pigging_checklist_id = fields.Many2one(
        comodel_name="pigging.equipment.checklist", string="Pigging Equipment Checklist", required=False, )


class PreConfirmationAssesment(models.Model):
    _name = 'preconfirmation.assesment'
    _rec_name = 'staff_id'
    _description = 'PreConfirmation Assesment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    staff_id = fields.Many2one(
        comodel_name="hr.employee", string="Name", required=False, )
    date_joined = fields.Date(string="Date Joined", required=False,)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department',)
    location = fields.Char(string="Location", required=False, )

    max_points = fields.Integer(string="MAX Points: 32", required=False, )

    recommendation = fields.Selection(string="Recomendation", selection=[('confirm', 'To be confirmed'), ('extend', 'Can be Extended'),
                                                                         ('terminate', 'Can be terminated'), ], required=False, )
    extension_period = fields.Selection(string="Choose periods to be extended",
                                        selection=[('three', '3 months'), ('six', '6 months'), ], required=False, )

    preconfirmation_assesment_ids = fields.One2many(comodel_name="preconfirmation.assesment.lines",
                                                    inverse_name="preconfirmation_assesment_id", string="Preconfirmation Assesment", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Validate'),
                                                         ('refuse', 'Refuse'), ('approved', 'Approved')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def confirm_request(self):
        self.state = 'confirm'

    @api.multi
    def validate_request(self):
        self.state = 'validate'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def approve_request(self):
        self.state = 'approved'


class PreConfirmationAssesmentLines(models.Model):
    _name = 'preconfirmation.assesment.lines'
    _description = 'PreConfirmation Assesment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    attributes = fields.Selection(string="Attributes", selection=[('1', 'Qualitative progress in work'),
                                                                  ('2', 'Commitment to work'), (
                                                                      '3', 'Ability to learn'),
                                                                  ('4', 'Initiative displayed'), (
                                                                      '5', 'Communication Skills'),
                                                                  ('6', 'Behaviour & Conduct in general'), (
                                                                      '7', 'Puncuality'),
                                                                  ('8', 'Temperament'), ], required=False, )

    score = fields.Selection(string="Grade", selection=[('vgood', 'V Good'), ('good', 'Good'),
                                                        ('avg', 'Average'), ('poor', 'Poor'),
                                                        ('unaccept', 'Unacceptable'), ], required=False, )

    preconfirmation_assesment_id = fields.Many2one(
        comodel_name="preconfirmation.assesment.lines", string="Preconfirmation Assesment", required=False, )


class LiftingPlan(models.Model):
    _name = 'lifting.plan'
    _rec_name = 'name'
    _description = 'Lifting Plan Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Location", required=True, )
    date = fields.Date(string="Date of Lift", required=False,
                       default=fields.Date.context_today)
    load_desc = fields.Char(string="Load Description", required=True, )
    life_desc = fields.Char(string="Life Description", required=True, )

    # Weight
    condition = fields.Selection(string="Equipment Condition", selection=[
                                 ('new', 'New'), ('used', 'Used'), ], required=False, )
    weight_empty = fields.Float(string="Weight Empty",  required=False, )
    weight_headche = fields.Float(
        string="Weight of Headche Ball",  required=False, )
    weight_block = fields.Float(string="Weight of Block",  required=False, )
    weight_lifting = fields.Float(
        string="Weight of Lifting Bar",  required=False, )
    weight_slings = fields.Float(
        string="Weight of Slings and Shackles",  required=False, )
    weight_jib_erect = fields.Float(
        string="Weight of JIB Erect",  required=False, )
    weight_jib_stored = fields.Float(
        string="Weight of JIB Stored",  required=False, )
    weight_headche_jib = fields.Float(
        string="Weight of Headche Ball on JIB",  required=False, )
    weight_cable = fields.Float(
        string="Weight of Cable (LOAD FALL)",  required=False, )
    allowance = fields.Float(
        string="ALLOWANCE FOR UNACCOUNTED MATERIAL IN EQUIPMENT",  required=False, )
    other = fields.Float(string="Other",  required=False, )
    total_weight = fields.Float(string="Total Weight",  required=False, )
    source_weight = fields.Char(
        string="Source of Load Weight", required=False, )
    verified_id = fields.Many2one(
        comodel_name="hr.employee", string="Weights Verified by:", required=False, )

    # JIB
    jib_erected = fields.Float(string="Erected",  required=False, )
    jib_stored = fields.Float(string="Stored",  required=False, )
    to_use = fields.Char(string="If JIB to be used", required=False, )
    jib_length = fields.Float(string="Length of JIB",  required=False, )
    jib_angle = fields.Float(string="Angle of JIB",  required=False, )
    jib_capacity = fields.Float(
        string="Rated Capacity of JIB (From Stored Chart)",  required=False, )

    # Crane Placement
    deviation = fields.Char(
        string="ANY DEVIATION FROM SMOOTH SOLID FOUNDATION IN THE AREA?", required=False, )
    electrical = fields.Char(
        string="ELECTRICAL HAZARDS IN THE AREA?", required=False, )
    obstacles = fields.Char(
        string="OBSTACLES OR OBSTRUCTIONS TO LIFT OR SWNG?", required=False, )
    swing = fields.Char(
        string="SWING DIRECTION AND DEGREE (BOOM SWING)", required=False, )

    # Cable
    parts_cable = fields.Integer(
        string="NUMBER OF PARTS OF CABLE", required=False, )
    size_cable = fields.Float(string="SIZE OF CABLE",  required=False, )

    # Sizing of Slings
    type = fields.Char(string="TYPE OF ARRANGEMENT", required=False, )
    no_slings = fields.Integer(
        string="NUMBER OF SLINGS IN HOOKUP", required=False, )
    sling_size = fields.Float(string="SLING SIZE",  required=False, )
    sling_length = fields.Float(string="SLING LENGTH",  required=False, )
    sling_capacity = fields.Float(
        string="RATED CAPACITY OF SLING",  required=False, )

    pin_diameter = fields.Float(
        string="PIN DIAMETER (INCHES",  required=False, )
    capacity_tons = fields.Float(string="CAPACITY (TONS)",  required=False, )
    shackle = fields.Char(
        string="SHACKLE ATTACHED TO LOAD BY", required=False, )
    no_shackle = fields.Integer(string="NUMBER OF SHACKLE", required=False, )

    # Crane
    type_crane = fields.Char(string="TYPE OF CRANE", required=False, )
    crane_capacity = fields.Float(string="CRANE CAPACITY",  required=False, )
    lift_arg = fields.Char(string="LIFTING AGREEMENT", required=False, )
    max_dist = fields.Float(
        string="MAXIMUM DISTANCE – CENTER OF LOAD TO CENTER PIN OF CRANE",  required=False, )
    boom = fields.Float(string="LENGTH OF BOOM",  required=False, )
    boom_pickup = fields.Float(
        string="ANGLE OF BOOM AT PICKUP",  required=False, )
    boom_set = fields.Float(string="ANGLE OF BOOM AT SET",  required=False, )
    crane_capacity = fields.Float(
        string="RATED CAPACITY OF CRANE UNDER SEVEREST",  required=False, )

    over_rear = fields.Float(string="OVER REAR",  required=False, )
    over_front = fields.Float(string="OVER FRONT",  required=False, )
    overside = fields.Float(string="OVERSIDE",  required=False, )
    cap_crane = fields.Float(
        string="FROM CHART- RATED CAPACITY OF CRANE FOR THIS LIFT",  required=False, )
    max_load = fields.Float(string="MAXIMUM LOAD ON CRANE",  required=False, )
    percentage = fields.Float(string="LIFT IS",  required=False, )

    # Pre-lift Checklist
    is_matting = fields.Boolean(string="MATTING ACCEPTACLE",)
    is_extended = fields.Boolean(string="OUTRIGGERS FULL EXTENDED",)
    is_good = fields.Boolean(string="CRANE IN GOOD CONDITION",)
    swing_room = fields.Boolean(string="SWING ROOM",)
    head_room = fields.Boolean(string="HEAD ROOM CHECKED",)
    counterweights = fields.Boolean(string="MAX COUNTERWEIGHTS USED",)
    has_tagline = fields.Boolean(string="TAG LINE USED",)
    is_experienced = fields.Boolean(string="EXPERIENCED OPERATOR",)
    is_flagman = fields.Boolean(string="EXPERIENCED FLAGMAN (DESIGNATED)",)
    is_rigger = fields.Boolean(string="EXPERIENCENED RIGGER",)
    has_load_chart = fields.Boolean(string="LOAD CHART IN CRANE",)
    wind = fields.Char(string="WIND CONDITION", required=False, )
    inspection_id = fields.Many2one(
        comodel_name="hr.employee", string="CRANE INSPECTED BY", required=False, )
    test_id = fields.Many2one(comodel_name="hr.employee",
                              string="FUNCTIONAL TEST OF CRANE BY", required=False, )

    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('task_sup', 'Task Supervisor'), ('rig_sup', 'Rigging Supervisor'),
                                                         ('refuse', 'Refuse'), ('hse', 'HSE')], default="draft",
                             track_visibility='onchange')

    @api.multi
    def task_sup_confirm(self):
        self.state = 'task_sup'

    @api.multi
    def rig_sup_confirm(self):
        self.state = 'rig_sup'

    @api.multi
    def refuse_request(self):
        self.state = 'refuse'

    @api.multi
    def hse_approval(self):
        self.state = 'hse'


class SiteInductionForm(models.Model):
    _name = 'site.induction.form'
    _rec_name = 'project_id'
    _description = 'Site Induction Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one(
        comodel_name='project.project', string='Project', required=True, )


class SiteInductionLines(models.Model):
    _name = 'site.induction.lines'
    _description = 'Site Induction Lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    topics = fields.Selection(string="Topic for Discussion", selection=[('1', 'Company HSE Policies Emergency Response Procedures'),
                                                                        ('2', 'Emergency Drills Reporting of Unsafe Acts/Conditions'),
                                                                        ('3', 'Near misses Journey Management Plan'),
                                                                        ('4', 'Site Security Horse play'),
                                                                        ('5', 'Company  Organogram Mustering Point'),
                                                                        ('6', 'HSE Meeting Toolbox Meeting'),
                                                                        ('7', 'Waste Management on Site Housekeeping'),
                                                                        ('8', 'Use of PPE Warning Signs'),
                                                                        ('9', 'Behavioral Base Safety Stop Work Authority'), ], required=False, )
    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Name", required=False, )
    date = fields.Date(string="Date", required=False,
                       default=fields.Date.context_today)
    comment = fields.Char(string="Comment", required=False, )


class PensionManager(models.Model):
    _name = 'pen.type'

    name = fields.Char(string='Name')
    contact_person = fields.Char(string='Contact person')
    phone = fields.Char(string='Phone Number')
    contact_address = fields.Text(string='Contact Address')
    pfa_id = fields.Char(string='PFA ID', required=True)
    email = fields.Char(string='Email')
    notes = fields.Text(string='Notes')


class LateArrivalForm(models.Model):
    _name = 'late.arrival.form'
    _description = 'Late Arrival Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('supervisor', 'Supervisor'),
        ('manager', 'HR Manager'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee Name', default=_default_employee)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', default=_default_department)
    job_title = fields.Char(
        string='Job Title', related='employee_id.job_title')
    date = fields.Datetime(string='Date & Time')
    reason_for_lateness = fields.Char(
        string='Please state the reason(s) for being late to work')
    informed_supervisor = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Did you inform your supervisor prior to late arrival')

    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    hr_approval = fields.Many2one(
        'res.users', 'HR Name', readonly=True, track_visibility='onchange')
    hr_approval_date = fields.Date(
        string='HR Date', readonly=True, track_visibility='onchange')

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'late.arrival.form') or '/'
        return super(LateArrivalForm, self).create(vals)

    @api.multi
    def button_submit(self):
        self.write({'state': 'supervisor'})
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Late Arrival Form '{}' for '{}' needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def alert_hr(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'hr.group_hr_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Late Arrival Form '{}' for '{}' has been approved by line manager, please review".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def action_line_manager_approval(self):
        self.write({'state': 'manager'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'hr.group_hr_manager')
        subject = "Late Arrival Form '{}' for '{}' has been approved by Line Manager".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for user in group_id.users:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        # self.alert_hr()

    @api.multi
    def button_hr_approval(self):
        self.write({'state': 'approve'})
        self.hr_approval_date = date.today()
        self.hr_approval = self._uid
        subject = "Late Arrival Form '{}' for '{}' has been approved by HR".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Late Arrival '{}'  for '{}' has been Rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class InsuranceLog(models.Model):
    _name = 'insurance.log'
    _description = 'Insurance Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Type of Policy', required=True)
    # policy_type = fields.Char(string='Policy Type', required=True)
    expiry_date = fields.Date(string='Expiry Date', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    renewal_date = fields.Date(string='Renewal Date', required=True)
    active = fields.Boolean(string='Active', default=True)

    @api.multi
    def alert_admin(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_admin')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Insurance Log '{}' has expired, please review".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def send_reminder_mail(self):
        test = False
        insurance_log = self.env['insurance.log'].search([])

        for self in insurance_log:
            if self.active == True:
                if self.exipry_date:
                    test = datetime.datetime.strptime(
                        str(self.exipry_date), "%Y-%m-%d")

                    insurance_log_day = test.day
                    insurance_log_month = test.month

                    today = datetime.datetime.now().strftime("%Y-%m-%d")

                    test_today = datetime.datetime.today().strptime(today, "%Y-%m-%d")
                    insurance_log_day_today = test_today.day
                    insurance_log_month_today = test_today.month

                    if insurance_log_month == insurance_log_month_today:
                        if insurance_log_day == insurance_log_day_today:
                            self.alert_admin()
        return


class OutgoingDocumentTemplate(models.Model):
    _name = 'outgoing.document.template'
    _description = 'Outgoing Document Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Description', required=True)
    destination = fields.Char(string='Destination', required=True)
    date_time_pickup = fields.Datetime(
        string='Date & Time of Pickup', required=True)
    sent_by = fields.Many2one(
        comodel_name='hr.employee', string='Sent By', required=True)
    authorization = fields.Char(string='Authorization')
    means_of_delivery = fields.Char(string='Means of Delivery')


class IncomingDocumentTemplate(models.Model):
    _name = 'incoming.document.template'
    _description = 'Incoming Document Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Description')
    recieved_by = fields.Char(string='Document received by')
    date_time_del = fields.Datetime(string='Date & Time of Delivery')
    issued_to = fields.Many2one(comodel_name='res.partner', string='Issued to')
    date_time = fields.Datetime(string='Date & Time')
    destination = fields.Char(string='Destination', required=True)


class CertificateforTendering(models.Model):
    _name = 'certificates.for.tendering'
    _description = 'Certificates For Tendering'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'New'),
        ('valid', 'Valid'),
        ('expired', 'Expired'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    name = fields.Char(string='Certificate', required=True)
    expiry_date = fields.Date(string='Expiry Date', required=True)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Renewal/Responsible party', required=True)
    tender_certificate_category_id = fields.Many2one(
        comodel_name='certificates.for.tendering.category', string='Cateogry')
    active = fields.Boolean(string='Active', default=True)

    @api.multi
    def update_status(self):
        exipry_date = datetime.datetime.strptime(
            str(self.expiry_date), "%Y-%m-%d")
        today = datetime.datetime.now()
        if today > exipry_date:
            self.write({'state': 'expired'})

    @api.multi
    def alert_bus_dev(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'sales_team.group_sale_salesman_all_leads')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Certificate for Tendering '{}' has expired, please review".format(
            self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def send_reminder_mail(self):
        test = False
        tender_certificate = self.env['certificates.for.tendering'].search([])

        for self in tender_certificate:
            if self.active == True:
                if self.expiry_date:
                    test = datetime.datetime.strptime(
                        str(self.expiry_date), "%Y-%m-%d")

                    insurance_log_day = test.day
                    insurance_log_month = test.month

                    today = datetime.datetime.now().strftime("%Y-%m-%d")

                    test_today = datetime.datetime.today().strptime(today, "%Y-%m-%d")
                    insurance_log_day_today = test_today.day
                    insurance_log_month_today = test_today.month

                    if insurance_log_month == insurance_log_month_today:
                        if insurance_log_day == insurance_log_day_today:
                            self.alert_bus_dev()
        return


class CertificateforTenderingCategory(models.Model):
    _name = 'certificates.for.tendering.category'

    name = fields.Char(string='Certificate', required=True)
    active = fields.Boolean(string='Active', default=True)


class JourneyRequest(models.Model):
    _name = 'journey.request'
    _description = 'Journey Request'
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

    state = fields.Selection([
        ('draft', 'New'),
        ('supervisor', 'Line Manager Approval'),
        ('manager', 'Logistics Manager Approval'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Requester:', required=True, default=_default_employee)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', required=True, default=_default_department)
    job_title = fields.Char(
        string='Job Title', related='employee_id.job_title')
    date_of_journey = fields.Date(string='Date of Journey', required=True)
    time_of_journey = fields.Float(string='Time of Journey', required=True)
    time_of_journey_am_pm = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')], string='AM/PM', copy=False)

    planned_returned_date = fields.Date(
        string='Planned Return Date', required=True)
    planned_returned_time = fields.Float(
        string='Planned Return Time', required=True)
    planned_returned_time_am_pm = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')], string='AM/PM', copy=False)

    purpose_of_journey = fields.Char(
        string='Purpose of Journey:', required=True)
    informed_supervisor = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Did you inform your supervisor prior to late arrival', required=True)
    destination = fields.Char(string='Destination:', required=True)

    supervisor_approval = fields.Many2one(
        'res.users', 'Authoriser Name', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string=' Authorisers Date', readonly=True, track_visibility='onchange')
    logistics_approval = fields.Many2one(
        'res.users', 'HR Name', readonly=True, track_visibility='onchange')
    logistics_approval_date = fields.Date(
        string='HR Date', readonly=True, track_visibility='onchange')
    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')
    vehicle_id = fields.Many2one(
        'fleet.vehicle', 'Assigned Vehicle', track_visibility='onchange')
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'journey.request') or '/'
        return super(JourneyRequest, self).create(vals)

    @api.multi
    def button_submit(self):
        self.write({'state': 'supervisor'})
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Journey Request '{}', for '{}' needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def alert_hr(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'hr.group_hr_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Journey Request '{}', for '{}' has been approved by line manager, please review".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def action_line_manager_approval(self):
        self.write({'state': 'manager'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'fleet.fleet_group_manager')
        subject = "Journey Request '{}', for '{}' has been approved by Line Manager".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for user in group_id.users:
            partner_ids.append(user.partner_id.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_logistics_approval(self):
        self.write({'state': 'approve'})
        self.logistics_approval_date = date.today()
        self.logistics_approval = self._uid
        subject = "Journey Request '{}', for '{}' has been approved by Logistics and assigned vehicle is '{}'".format(
            self.name, self.employee_id.name, self.vehicle_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Journey Request '{}', for '{}' has been Rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def set_draft(self):
        self.state = 'draft'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    "You are not allowed to delete non-draft records!")
        return super(JourneyRequest, self).unlink()


class CalibrationLog(models.Model):
    _name = 'calibration.log'
    _description = 'Calibration Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    type_of_calibration_log_id = fields.Many2one(
        comodel_name='type.calibration.log', string='Type of Calibration Log:', required=True)
    number = fields.Integer(string='S/N',  compute='_compute_sn')
    name = fields.Char(string='Equipment Name and other Identification',
                       required=True, index=True, copy=False)
    calibration_carried_out = fields.Char(
        string='Type of Calibration Carried out', required=True)
    calibrated_by_id = fields.Many2one(
        comodel_name='hr.employee', string='Calibrated By:', required=True)
    date_last_calibration = fields.Datetime(
        string='Date last Calibration', required=True)
    calibration_next_due = fields.Datetime(
        string='Calibration Next Due', required=True)
    remarks = fields.Char(string='Remarks')

    @api.depends('type_of_calibration_log_id', 'type_of_calibration_log_id.next_number')
    def _compute_sn(self):
        for type in self.type_of_calibration_log_id:
            self.number = type.next_number
            type.update({
                'next_number': self.number + 1,
            })
            type.next_number = self.number + 1


class TypeCalibrationLog(models.Model):
    _name = 'type.calibration.log'
    _description = 'Type of Calibration Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Type of Calibration',
                       required=True, index=True, copy=False, default='New')
    next_number = fields.Integer(string='S/N')
    active = fields.Boolean(string='Active', default=True)


class TenderAnalysis(models.Model):
    _name = 'tender.analysis'
    _description = 'Tender Analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    type = fields.Selection([
        ('successful', 'Successful'),
        ('unsuccessful', 'Unsuccessful'),
    ], string='Type', readonly=True, index=True, copy=False, track_visibility='onchange')

    state = fields.Selection([
        ('T_C', 'T&C'),
        ('tc', 'T/C'),
        ('t', 'T'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    name = fields.Char(string='TENDER DESCRIPTION', required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='CLIENT', required=True)
    source = fields.Char(string='SOURCE')
    tender_number = fields.Char(string="TENDER NUMBER")
    date_submitted = fields.Datetime(string="DATE SUBMITTED")
    comments = fields.Char(string="COMMENTS")
    corrective_action = fields.Char(string="CORRECTIVE ACTION")


class TenderMonitoringSheet(models.Model):
    _name = 'tender.monitoring.sheet'
    _description = 'Tender Monitoring Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    tender_id = fields.Many2one(
        comodel_name='type.tender.monitoring.sheet', string='Tender', required=True)

    name = fields.Char(string='TENDER DESCRIPTION', required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='CLIENT', required=True)
    state = fields.Selection([
        ('T_C', 'T&C'),
        ('tc', 'T/C'),
        ('t', 'T'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')
    source = fields.Char(string='SOURCE')
    tender_number = fields.Char(string="TENDER NUMBER")
    date_submitted = fields.Datetime(string="DATE SUBMITTED")
    comments = fields.Char(string="COMMENTS")


class TypeTenderMonitoringSheet(models.Model):
    _name = 'type.tender.monitoring.sheet'
    _description = 'Type of Tender'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tender', required=True,
                       index=True, copy=False, default='New')
    active = fields.Boolean(string='Active', default=True)


class VehicleMovementRegister(models.Model):
    _name = 'vehicle.movement.register'
    _description = 'Vehicle Movement Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    driver_id = fields.Many2one(
        comodel_name='hr.employee', string='Driver’s Name', required=True)
    vehicle_no = fields.Many2one(
        comodel_name='fleet.vehicle', string='Vehicle No', required=True)
    proceeding_to = fields.Char(string='Proceeding to', required=True)
    requester_id = fields.Many2one(
        comodel_name='hr.employee', string='Name of Requester', required=True)
    time_out = fields.Float(string='TIme Out')
    mileage_out = fields.Float(string='Mileage Out')
    gas_level_out = fields.Float(string='Gas Level (Liters)')
    time_in = fields.Float(string='TIme In')
    mileage_in = fields.Float(string='Mileage In')
    gas_level_in = fields.Float(string='Gas Level (Liters)')
    date = fields.Date(string='Date', default=date.today())


class ExitForm(models.Model):
    _name = 'exit.form'
    _description = 'Exit Form (Working Hours)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.name

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('supervisor', 'Line Manager'),
        ('manager', 'HR Manager'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Applicants’s Name', required=True, default=_default_employee)
    applicant_function = fields.Char(
        string='Applicants’s Function', required=True, default=_default_department)
    purpose_of_exit = fields.Char(string='Purpose of Exit', required=True)
    time_of_leaving = fields.Float(string='Time of Leaving', required=True)
    time_of_returrning = fields.Float(
        string='Time of Returning', required=True)
    date = fields.Date(string="Date")
    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    hr_approval = fields.Many2one(
        'res.users', 'HR Name', readonly=True, track_visibility='onchange')
    hr_approval_date = fields.Date(
        string='HR Date', readonly=True, track_visibility='onchange')

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'exit.form') or '/'
        return super(ExitForm, self).create(vals)

    @api.multi
    def button_submit(self):
        self.write({'state': 'supervisor'})
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Exit Form '{}' for '{}' needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def action_line_manager_approval(self):
        self.write({'state': 'manager'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'hr.group_hr_manager')
        subject = "Exit Form '{}' for '{}' has been approved by Line Manager".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_hr_approval(self):
        self.write({'state': 'approve'})
        self.hr_approval_date = date.today()
        self.hr_approval = self._uid
        subject = "Exit Form '{}' for '{}' has been approved by HR".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Exit Form '{}' for '{}' has been Rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class AbsenseInformation(models.Model):
    _name = 'absense.information'
    _description = 'Absense Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('supervisor', 'HOD Approval'),
        ('manager', 'HR Manager'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee’s Name', required=True, default=_default_employee)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', required=True, default=_default_department)
    type_of_absense = fields.Selection([
        ('sick', 'Sick'),
        ('maternity_paternity', 'Maternity/Paternity'),
        ('bereavement', 'Bereavement'),
        ('other', 'Other'),
    ], string='Type of Absense Requested', required=True, copy=False, track_visibility='onchange')
    date_absense_from = fields.Datetime(
        string='Date of Absense From', required=True)
    date_absense_to = fields.Datetime(
        string='Date of Absense To', required=True)
    reason_for_absense = fields.Char(string='Reason of Absense', required=True)
    comments = fields.Char(string='Comments')

    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')
    hr_approval = fields.Many2one(
        'res.users', 'HR Name', readonly=True, track_visibility='onchange')
    hr_approval_date = fields.Date(
        string='HR Date', readonly=True, track_visibility='onchange')

    @api.multi
    def button_submit(self):
        self.write({'state': 'supervisor'})
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Absense Request for '{}' needs approval".format(
            self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_approval(self):
        self.write({'state': 'manager'})
        self.supervisor_approval_date = date.today()
        self.supervisor_approval = self._uid
        subject = "Absense Request for '{}' has been approved by HOD".format(
            self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_hr_approval(self):
        self.write({'state': 'approve'})
        self.hr_approval_date = date.today()
        self.hr_approval = self._uid
        subject = "Absense Request for '{}' has been approved by HR".format(
            self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Absense Request for '{}' has been Rejected".format(
            self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class InternetDowntimeRegister(models.Model):
    _name = 'internet.downtime.register'
    _description = 'Internet Downtime Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date = fields.Date(string='Date', required=True)
    downtime = fields.Float(string='Down Time', required=True)
    uptime = fields.Float(string='Up Time', required=True)
    duration = fields.Float(string='Duration of Downtime (Hrs)')
    issue = fields.Char(string='Issue')
    resolutions = fields.Char(string='Resolution')

    downtime_am_pm = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')], string='AM/PM', copy=False)
    uptime_am_pm = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')], string='AM/PM', copy=False)


class MSOfficeDeployment(models.Model):
    _name = 'ms.office.deployment'
    _description = 'MS Office Deployment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='NAME', required=True)
    device_type = fields.Char(string='DEVICE TYPE', required=True)
    asset_number = fields.Char(string='ASSET NUMBER', required=True)
    key_in_use = fields.Char(string='KEY IN USE', required=True)
    status = fields.Char(string='STATUS', required=True)
    remark = fields.Char(string='REMARK', required=True)


class AntivirusTrackerRenewal(models.Model):
    _name = 'antivirus.tracker.renewal'
    _description = 'ANTIVIRUS TRACKER/ RENEWAL'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='NAME', required=True,
                       track_visibility='onchange')
    type_of_device = fields.Selection([
        ('desktop', 'Desktop'),
        ('laptop', 'Laptop'),
    ], string='DESKTOP / LAPTOP', required=True, copy=False, track_visibility='onchange')
    asset_number = fields.Char(string='ASSET NUMBER', required=True)
    renewal_date = fields.Date(string='DATE OF RENEWAL', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    type = fields.Char(string='Type', required=True)
    status = fields.Char(string='STATUS', required=True)
    remark = fields.Char(string='REMARK', required=True)


class PlannedPreventiveMaintenance(models.Model):
    _name = 'planned.preventive.maintenance'
    _description = 'Planned Preventive Maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    equipment_id = fields.Char(string='Equipment', required=True)
    asset_number = fields.Char(string='ASSET NUMBER', required=True)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', required=True, default=_default_department)
    preventive_action = fields.Char(
        string='Preventive Maintenance Action', required=True)
    schedule = fields.Char(string='Schedule', required=True)
    next_due_date = fields.Date(string='Next due date', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    action_party = fields.Char(string='Action Party', required=True)
    contingency_plan = fields.Char(string='Contingency plan', required=True)


class EquipmentMaintenanceRegister(models.Model):
    _name = 'equipment.maintenance.register'
    _description = 'Equipment Maintenance Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    equipment_id = fields.Char(string='Equipment', required=True)
    asset_number = fields.Char(string='ASSET NUMBER', required=True)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', required=True)
    fault_status = fields.Char(string='Fault Status', required=True)
    repair_status = fields.Char(string='Repair Status', required=True)
    repair_date = fields.Date(string='Repair Date', required=True)
    cost = fields.Float(string='Cost')
    routine_check = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Routine Check', required=True, copy=False, track_visibility='onchange')


class ICTPaidServices(models.Model):
    _name = 'ict.paid.services'
    _description = 'ICT Paid Services'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Services', required=True,
                       track_visibility='onchange')
    sub = fields.Char(string='Subscription', required=True,
                      track_visibility='onchange')
    cost = fields.Float(string='Cost')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency')
    renewal_date = fields.Date(string='Date of Renewal', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    status = fields.Char(string='STATUS', required=True)

    @api.multi
    def send_reminder_notification(self):
        reminders = self.env['ict.paid.services'].search([])

        current_dates = False

        for self in reminders:
            if self.due_date:

                current_dates = datetime.datetime.strptime(
                    str(self.due_date), "%Y-%m-%d")
                current_datesz = current_dates - relativedelta(days=6)

                date_start_day = current_datesz.day
                date_start_month = current_datesz.month
                date_start_year = current_datesz.year

                today = datetime.datetime.now().strftime("%Y-%m-%d")

                test_today = datetime.datetime.today().strptime(today, "%Y-%m-%d")
                date_start_day_today = test_today.day
                date_start_month_today = test_today.month
                date_start_year_today = test_today.year

                if date_start_month == date_start_month_today:
                    if date_start_day == date_start_day_today:
                        if date_start_year == date_start_year_today:
                            self.send_the_reminder_notification()
        return

    @api.multi
    def send_the_reminder_notification(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'helpdesk.group_helpdesk_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        # subject = "This is a reminder for '{}', {}".format(self.name, self.comments)
        subject = "This is a reminder for '{}', which is due tomorrow".format(
            self.name)
        # body = self.comments
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False
        return {}


class MdrForms(models.Model):
    _name = 'mdr.forms'
    _description = 'MDR Forms'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Document Title',
                       required=True, track_visibility='onchange')
    doc_no = fields.Char(string='Document No.',
                         required=True, track_visibility='onchange')
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', track_visibility='onchange')
    rev_no = fields.Char(string='Rev No.', track_visibility='onchange')
    issue_date = fields.Date(string='Issue Date', track_visibility='onchange')


class ReceivingInspectionReport(models.Model):
    _name = 'receiving.inspection.report'
    _description = 'Receiving Inspection Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'New'),
        ('approve', 'Approved'),
        ('awaiting_verification', 'Awaiting Verification'),
        ('verify', 'Verified'),
        ('reject', 'Rejected'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'receiving.inspection.report') or '/'
        return super(ReceivingInspectionReport, self).create(vals)

    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Vendor', track_visibility='onchange')

    location_id = fields.Char(string='Location.', track_visibility='onchange')

    receiving_inspection_report_line_ids = fields.One2many(
        'receiving.inspection.report.lines', 'receiving_inspection_report_id', string="Receiving Inspection Report Lines", copy=True)

    manufactured_by_specified_manufacturer_comment = fields.Char(
        string='Verify if product was manufactured by specified manufacturer/distributor and tested as required', required=False, track_visibility='onchange')
    manufactured_by_specified_manufacturer = fields.Boolean(
        string='Verify if product was manufactured by specified manufacturer/distributor and tested as required', required=True, track_visibility='onchange')
    vendor_topline_approved_list_comment = fields.Char(
        string='Confirm that vendor is on the Topline approved list, if not, confirm reason(s) for usage', required=False, track_visibility='onchange')
    vendor_topline_approved_list = fields.Boolean(
        string='Confirm that vendor is on the Topline approved list, if not, confirm reason(s) for usage', required=True, track_visibility='onchange')
    incorporated_noted_instructions_comment = fields.Char(
        string='Verify that items incorporated noted instructions per purchase order', required=False, track_visibility='onchange')
    incorporated_noted_instructions = fields.Boolean(
        string='Verify that items incorporated noted instructions per purchase order', required=True, track_visibility='onchange')
    confirm_delivery_time_date_comment = fields.Char(
        string='Confirm delivery time/date as specified in the request', required=False, track_visibility='onchange')
    confirm_delivery_time_date = fields.Boolean(
        string='Confirm delivery time/date as specified in the request', required=True, track_visibility='onchange')
    item_matches_product_description_comment = fields.Char(
        string='Verify that item matches product description', required=False, track_visibility='onchange')
    item_matches_product_description = fields.Boolean(
        string='Verify that item matches product description', required=True, track_visibility='onchange')
    item_quantity_correct_comment = fields.Char(
        string='Confirm that item quantity is correct', required=False, track_visibility='onchange')
    item_quantity_correct = fields.Boolean(
        string='Confirm that item quantity is correct', required=True, track_visibility='onchange')

    remarks = fields.Char(string='Remarks', track_visibility='onchange')

    approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange', copy=False)
    manager_approval = fields.Many2one(
        'res.users', 'Topline Qa/Qc', readonly=True, track_visibility='onchange', copy=False)

    date_verification = fields.Date(
        string='Date of Verification', track_visibility='onchange', copy=False)
    verification_approval = fields.Many2one(
        'res.users', 'Verified By (End User):', readonly=True, track_visibility='onchange', copy=False)
    end_user_ids = fields.Many2many(
        comodel_name='res.users', string='End User(s)', copy=False)

    @api.multi
    def button_accept(self):
        self.write({'state': 'approve'})
        self.approval_date = date.today()
        self.manager_approval = self._uid

    @api.multi
    def button_verify(self):
        self.write({'state': 'verify'})
        self.date_verification = date.today()
        self.verification_approval = self._uid

    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})

    @api.multi
    def button_reset(self):
        self.write({'state': 'draft'})

    @api.multi
    def button_awaiting_verification(self):
        self.write({'state': 'awaiting_verification'})


class ReceivingInspectionReportLines(models.Model):
    _name = 'receiving.inspection.report.lines'

    receiving_inspection_report_id = fields.Many2one(
        comodel_name='receiving.inspection.report', string='Receiving Inspection Report')

    product_id = fields.Many2one(
        comodel_name='product.template', string='Product')
    name = fields.Char(string='Item Description', required=True)
    qty = fields.Float(string='Quantity', required=True)
    defects = fields.Char(string='Defects/Non-Conformance', required=False)
    type_verification = fields.Char(
        string='Type of Verification', required=False)

    @api.onchange('product_id')
    def _onchange_partner_id(self):
        self.name = self.product_id.name


class ReceivingInspectionReportVerification(models.TransientModel):
    _name = 'receiving.inspection.report.verification'
    _description = 'Get Verification Personnels'

    end_user_ids = fields.Many2many(
        comodel_name='res.users', string='End Users')

    @api.multi
    def action_receiving_inspection_report_submit(self):
        receiving_inspection_report = self.env['receiving.inspection.report'].browse(
            self.env.context.get('active_ids'))
        receiving_inspection_report.end_user_ids = self.end_user_ids
        partner_ids = []
        if receiving_inspection_report.end_user_ids:
            for user in receiving_inspection_report.end_user_ids:
                partner_ids.append(user.partner_id.id)
        receiving_inspection_report.message_subscribe(partner_ids=partner_ids)
        subject = "Receiving Inspection Report {} needs Verification".format(
            receiving_inspection_report.name)
        receiving_inspection_report.message_post(
            subject=subject, body=subject, partner_ids=partner_ids)

        return receiving_inspection_report.button_awaiting_verification()


class PrcForms(models.Model):
    _name = 'prc.forms'
    _description = 'PRC Forms'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Document Title',
                       required=True, track_visibility='onchange')
    doc_ref = fields.Char(string='Document Ref No.',
                          required=True, track_visibility='onchange')
    doc_type = fields.Char(string='Document Type.',
                           required=True, track_visibility='onchange')
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', track_visibility='onchange')
    rev_no = fields.Char(string='Rev No.', track_visibility='onchange')
    review_date = fields.Date(string='Review Date',
                              track_visibility='onchange')
    status = fields.Char(string='Status', required=True,
                         track_visibility='onchange')
    remark = fields.Char(string='Remark.', required=True,
                         track_visibility='onchange')


class ProjectMonitoringSheet(models.Model):
    _name = 'project.monitoring.sheet'
    _description = 'Project Monitoring Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Project Title', required=True,
                       track_visibility='onchange')
    project_id = fields.Many2one(
        comodel_name='project.project', string='Relating Project', track_visibility='onchange')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Client', track_visibility='onchange')
    mob_date = fields.Date(string='Mobilization Date',
                           track_visibility='onchange')
    demob_date = fields.Date(
        string='Demobilization Date', track_visibility='onchange')

    close_out_status = fields.Char(
        string='Close Out Report', track_visibility='onchange')
    client_feedback_status = fields.Char(
        string='Client Feedback', track_visibility='onchange')
    lessons_learnt_status = fields.Char(
        string='Lessons Learnt', track_visibility='onchange')

    remark = fields.Char(string='remark', track_visibility='onchange')


class ClientFeedbackLog(models.Model):
    _name = 'client.feedback.log'
    _description = 'Client Feedback Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Project Title', required=True,
                       track_visibility='onchange')
    project_id = fields.Many2one(
        comodel_name='project.project', string='Relating Project', track_visibility='onchange')

    overall_project_outcome = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ], string='Overall Project Outcome', required=True)

    communication = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ], string='Communication', required=True)

    project_leader = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ], string='Project Leader', required=True)

    staff_competence = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ], string='Staff Competence', required=True)

    delivery_time = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ], string='Delivery Time', required=True)

    quality_project_outcome = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ], string='Quality of Project Outcome', required=True)


class ClientComplaintsLog(models.Model):
    _name = 'client.complaints.log'
    _description = 'Client Complaints Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(
        comodel_name='res.partner', required=True, string='Client', track_visibility='onchange')
    name = fields.Char(string='Project Title', required=True,
                       track_visibility='onchange')
    project_id = fields.Many2one(
        comodel_name='project.project', string='Relating Project', track_visibility='onchange')
    date_complaint = fields.Date(
        string='Date Complaint', required=True, track_visibility='onchange')
    description = fields.Char(
        string='Description of Complaint', required=True, track_visibility='onchange')
    root_cause = fields.Char(string='Root Cause', track_visibility='onchange')
    action_taken = fields.Char(
        string='Action Taken', track_visibility='onchange')
    date_closed = fields.Date(
        string='Date Closed/Result', track_visibility='onchange')


class QAQCVendorsFacilityAuditChecklist(models.Model):
    _name = 'qaqc.vendors.facility.audit.checklist'
    _description = 'QAQC Vendors Facility Audit Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'New'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    partner_id = fields.Many2one(
        comodel_name='res.partner', required=True, string='Company Name', track_visibility='onchange')

    cac_docs_provided = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Have CAC documents been provided', required=True)
    current_income_taxclearance_certificate_provided = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Has current income TAX clearance certificate been provided', required=True)
    established_quality_program = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there an established Quality Program? If yes, is there an up-to-date Quality Manual?', required=True)
    workmen_conpensation = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Has current workmen compensation insurance/third party liability been provided', required=True)
    evidence_equipment_ownership = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Has MOU/evidence of equipment ownership been provided', required=True)
    evidence_operator = fields.Selection([('yes', 'YES'), ('no', 'NO'), ('n_a', 'N/A')],
                                         string='Has evidence of Operator/Employee competence been provided', required=True)
    approved_vendor_list = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there an approved vendor list available to the purchasing unit which ensures all suppliers (vendor, distributors and subcontractors) to thisorganization meet quality standards, undergo periodic surveillance and auditing, and provide products in accordance with applicable quality standards?', required=True)
    individual_training_plans = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Do individual training plans and training records exist?', required=True)
    approved_preventive_maintenance = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there an approved Preventive Maintenance/ Calibration Program?', required=True)
    approved_equipment_operating_procedure = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there an approved Equipment Operating Procedure', required=True)
    necessary_equipment_certified_fit = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Are the necessary equipment certified fit for use', required=True)
    equipment_physically_sighted = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Were the required equipment physically sighted', required=True)
    equipment_equipped_with_loading_offloading_apparatus = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Are the necessary equipment equipped with loading, offloading apparatus (e.g belts, slings, chains etc)', required=True)
    defined_communication_path_for_product = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there a defined communication path for product/ service delivery, mode of delivery and delivery dates? (e.g. emails, telephone etc.)', required=True)
    storage_workshop_kept_in_order = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is the storage area/workshop kept in order, clean and maintained', required=True)
    safety_apparatus_provided_operator = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Are safety apparatus provided for the Operator/employee', required=True)
    general_contractor_attitude = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is general contractor attitude satisfactory', required=True)
    valid_evidence_road_statutory_requirement_compliance = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there a valid evidence of Road Statutory Requirement Compliance', required=True)
    approved_logistics_management_procedure = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there an approved Logistics Management Procedure', required=True)

    adequate_system_documented = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there adequate system documented and in use to ensure no item will be sold past the expiration date?', required=True)
    packaging_procedure = fields.Selection([('yes', 'YES'), ('no', 'NO'), ('n_a', 'N/A')],
                                           string='Is there a packaging procedure or system that provides appropriate protection against damage?', required=True)
    warranties_claim_policies = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Are there warranties and claim policies in place?', required=True)
    adequate_administrative_documents = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Are there adequate administrative documents in place (invoices, waybill, certificate of conformity, customs documents, bills of laden)?', required=True)
    storage_facilities_appropriate_environmental_conditions = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Are storage facilities appropriate for environmental conditions such as temperature and humidity?', required=True)
    periodically_detect_possible_deterioration = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is there a method or system to check items in storage periodically to detect possible deterioration?', required=True)
    packaging_provide_clear_description = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Does the packaging provide a clear description of the content', required=True)
    protection_provided_quality = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is protection provided for the quality of product during shipping and other phases of delivery?', required=True)
    control_provided_identification = fields.Selection([('yes', 'YES'), ('no', 'NO'), (
        'n_a', 'N/A')], string='Is control provided for identification, documentation, evaluation, segregation and appropriate disposition of nonconforming products?', required=True)

    accepted = fields.Selection(
        [('yes', 'YES'), ('no', 'NO')], string='Accepted', required=True)
    comment = fields.Char(string='Comment', track_visibility='onchange')

    audit_date = fields.Date(string='Audited Date',
                             readonly=True, track_visibility='onchange')
    audit_approval = fields.Many2one(
        'res.users', 'Audited By', readonly=True, track_visibility='onchange')

    approval_date = fields.Date(
        string='Approved Date', readonly=True, track_visibility='onchange')
    manager_approval = fields.Many2one(
        'res.users', 'Approved By', readonly=True, track_visibility='onchange')

    @api.multi
    def button_audit_approve(self):
        # self.write({'state':'approve'})
        self.audit_date = date.today()
        self.audit_approval = self._uid

    @api.multi
    def button_approve(self):
        self.write({'state': 'approve'})
        self.approval_date = date.today()
        self.manager_approval = self._uid

    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})


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
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    atp_form_line_ids = fields.One2many(
        'atp.form.lines', 'atp_form_id', string="ATP Form Lines", copy=True)

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')
    date = fields.Date(string='Date', required=True,
                       track_visibility='onchange', default=date.today())
    project_des = fields.Char(string='Project Title',
                              required=True, track_visibility='onchange')
    project_id = fields.Many2one(
        comodel_name='project.project', string='Relating Project', track_visibility='onchange')
    remark = fields.Char(string='Remark', required=False)
    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking', string='Inventory Operation', track_visibility='onchange')

    expected_date = fields.Date(
        string='Expected Date of Arrival', track_visibility='onchange')

    total = fields.Float(string='Total', compute='_total_unit', readonly=True)

    po_count = fields.Integer(
        compute="_po_count", string="RFQ's/PO's", store=False)

    payment_req_count = fields.Integer(
        compute="_payr_count", string="Payment Requisitions", store=False)

    stock_source = fields.Char(string='Source', copy=False)

    @api.multi
    def name_get(self):
        res = []
        for atp in self:
            result = atp.name
            if atp.stock_source:
                result = str(atp.name) + " " + "-" + \
                    " " + str(atp.stock_source)
            res.append((atp.id, result))
        return res

    @api.multi
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
            'context': {'default_stock_source': self.name, 'default_order_line': order_lines}
        }

    @api.multi
    def create_purchase_order2(self):
        """
        Method to open create atp form
        """

        # partner_id = self.client_id
        # client_id = self.client_id
        # store_request_id = self.id
        # sub_account_id = self.sub_account_id
        # product_id = self.move_lines.product_id

        view_ref = self.env['ir.model.data'].get_object_reference(
            'purchase', 'purchase_order_form')
        view_id = view_ref[1] if view_ref else False

        for subscription in self:
            order_lines = []
            for line in subscription.atp_form_line_ids:
                order_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_id': line.product_id.id,
                    'account_id': line.product_id.property_account_expense_id.id,
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

    @api.multi
    def create_payment_requisition(self):
        """
        Method to open create payment requisition
        """
        view_ref = self.env['ir.model.data'].get_object_reference(
            'topline', 'topline_payment_requisition_form_view')
        view_id = view_ref[1] if view_ref else False

        for subscription in self:
            order_lines = []
            for line in subscription.atp_form_line_ids:
                order_lines.append((0, 0, {
                    'name': line.name,
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

    @api.multi
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

    @api.multi
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

    @api.multi
    def open_po(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('atp_id', '=', self.id))
        return action

    @api.multi
    def open_payr(self):
        self.ensure_one()
        action = self.env.ref(
            'topline.topline_payment_requisition_form_action').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('atp_id', '=', self.id))
        return action

    @api.one
    @api.depends('atp_form_line_ids.price')
    def _total_unit(self):
        for line in self.atp_form_line_ids:
            self.total += line.price_subtotal

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'atp.form') or '/'
        return super(ATPform, self).create(vals)

    @api.multi
    def button_submit(self):
        self.write({'state': 'submit'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
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

    @api.multi
    def button_approval(self):
        self.write({'state': 'approve'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
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

    @api.multi
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
    ], string='Certificate Required', readonly=False, index=True, copy=False, track_visibility='onchange')

    price = fields.Float(string='Est. Price', required=False)

    @api.onchange('product_id')
    def _onchange_partner_id(self):
        self.name = self.product_id.name
        self.price = self.product_id.standard_price

    price_subtotal = fields.Float(
        string='Est. Price Subtotal', readonly=True, compute='_price_subtotal')

    @api.one
    def _price_subtotal(self):
        for line in self:
            self.price_subtotal = line.price * line.qty


class TravelReport(models.Model):
    _name = 'travel.report'
    _description = 'Travel Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    date_booking = fields.Date(
        string='Date of Booking', required=True, track_visibility='onchange')
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Name', track_visibility='onchange')
    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    related='employee_id.department_id', track_visibility='onchange')
    from_des = fields.Char(string='From', required=True,
                           track_visibility='onchange')
    to_des = fields.Char(string='TO', required=True,
                         track_visibility='onchange')
    reason = fields.Char(string='Reason', required=True,
                         track_visibility='onchange')
    cost = fields.Float(string='Cost(N)', required=True,
                        track_visibility='onchange')
    type = fields.Char(string='Type', track_visibility='onchange')
    remark = fields.Char(string='Remark', track_visibility='onchange')


class StationeryReport(models.Model):
    _name = 'stationery.report'
    _description = 'Stationery Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date = fields.Date(string='Date', required=True,
                       track_visibility='onchange')
    product_id = fields.Many2one(
        comodel_name='product.template', string='Product')
    name = fields.Char(string='Item/Stationery',
                       required=True, track_visibility='onchange')
    qty = fields.Float(string='Quantity', required=True,
                       track_visibility='onchange')
    employee_id = fields.Many2one(
        comodel_name='hr.employee', required=True, string='Name', track_visibility='onchange')
    location = fields.Char(string='Location', required=True,
                           track_visibility='onchange')


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

    @api.multi
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
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    employee_id = fields.Many2one(comodel_name='hr.employee', required=True,
                                  string='Name', track_visibility='onchange', default=_default_employee)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    related='employee_id.department_id', track_visibility='onchange')
    job_title = fields.Char(
        string='Job Title', related='employee_id.job_title', track_visibility='onchange')

    advance_of = fields.Float(
        string='Advance of', required=True, track_visibility='onchange')
    month_of = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                                 ('5', 'May'), ('6', 'June'), ('7',
                                                               'July'), ('8', 'August'),
                                 ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                                string='Month of', required=True, track_visibility='onchange')
    pay_off_month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                                      ('5', 'May'), ('6', 'June'), ('7',
                                                                    'July'), ('8', 'August'),
                                      ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                                     string='Month', required=True, track_visibility='onchange')

    employee_name = fields.Many2one(
        'res.users', 'Employee Name', readonly=True, track_visibility='onchange')
    employee_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    finance_comments = fields.Char(
        string='Comments', track_visibility='onchange')
    finance_approval = fields.Many2one(
        'res.users', 'Account Manager Name', readonly=True, track_visibility='onchange')
    finance_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'salary.advance') or '/'
        return super(SalaryAdvanceForm, self).create(vals)

    @api.multi
    def button_submit(self):
        self.write({'state': 'submit'})
        self.employee_approval_date = date.today()
        self.employee_name = self._uid
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

    @api.multi
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
        subject = "Salary Advance '{}', for {} has been approved by supervisor and needs approval from Audit".format(
            self.name, self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
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
        subject = "Salary Advance '{}', for '{}' needs approval from MD".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
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
        subject = "Salary Advance '{}', for '{}' has been approved by MD and needs approval from Finance".format(
            self.name,  self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
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

    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Salary Advance '{}' for {} has been rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_requisition_id = fields.Many2one(
        'payment.requisition.form', string='Payment Requisition', copy=False, help="Payment Requisition where the move line come from")

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(AccountMoveLine, self).reconcile(
            writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        account_move_ids = [l.move_id.id for l in self if float_compare(
            l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        if account_move_ids:
            expense_sheets = self.env['hr.expense.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            expense_sheets.set_to_paid()
        return res


class MissingStolenAssetReportForm(models.Model):
    _name = 'missing.stolen.asset.report.form'
    _description = 'Missing/Stolen Asset Report Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Reported'),
        ('finance_approve', 'Finance Review'),
        ('approve', 'Finance Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    name_ref = fields.Char('Order Reference', readonly=True,
                           required=True, index=True, copy=False, default='New')

    @api.multi
    def _check_manager_approval(self):
        current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id
        if self.employee_id.user_id == self.env.user:
            raise UserError(_("You cannot approve your own Request"))

        if not self.env.user in current_managers:
            raise UserError(_("You can only approve your department expenses"))

    @api.model
    def create(self, vals):
        if vals.get('name_ref', 'New') == 'New':
            vals['name_ref'] = self.env['ir.sequence'].next_by_code(
                'missing.stolen.asset.report') or '/'
        return super(MissingStolenAssetReportForm, self).create(vals)

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    employee_id = fields.Many2one(comodel_name='hr.employee', required=True,
                                  string='Name', track_visibility='onchange', default=_default_employee)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    related='employee_id.department_id', track_visibility='onchange')

    name = fields.Char(string='Asset Description', required=True)
    serial_no = fields.Char(string='serial/Asset number', required=True)
    cost_asset = fields.Float(string='Cost of Asset')
    book_value = fields.Float(string='Book Value')

    last_known_location = fields.Char(string='Last Known Location and Data')
    incident_lead_misplacement = fields.Char(
        string='Incident That Led to Misplacement:')

    employee_name = fields.Many2one(
        'res.users', 'Reported By', readonly=True, track_visibility='onchange')
    employee_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    store_approval = fields.Many2one(
        'res.users', 'Store Officer’s Name', readonly=True, track_visibility='onchange')
    store_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    finance_approval = fields.Many2one(
        'res.users', 'Account Manager’s Name', readonly=True, track_visibility='onchange')
    finance_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    @api.multi
    def button_submit_report(self):
        self.write({'state': 'submit'})
        self.employee_approval_date = date.today()
        self.employee_name = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'stock.group_stock_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Missing/Stolen Asset '{}' for '{}' has been reported".format(
            self.name_ref, self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_store_report(self):
        self._check_manager_approval()
        self.write({'state': 'finance_approve'})
        self.finance_approval_date = date.today()
        self.finance_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_finance_manager')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Missing/Stolen Asset '{}' for '{}' has been validated by store".format(
            self.name_ref, self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    @api.multi
    def button_finance_approval(self):
        self.write({'state': 'approve'})
        self.finance_approval_date = date.today()
        self.finance_approval = self._uid
        subject = "Missing/Stolen Asset '{}' for  '{}' has been approved by Finance".format(
            self.name_ref, self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Missing/Stolen Asset '{}' for  '{}' has been rejected".format(
            self.name_ref, self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


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
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cash.advance.request') or '/'
        return super(CashAdvanceRequestForm, self).create(vals)

    @api.multi
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
                       track_visibility='onchange', default=date.today())
    employee_id = fields.Many2one(comodel_name='hr.employee', required=True,
                                  string='Name', track_visibility='onchange', default=_default_employee)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    related='employee_id.department_id', track_visibility='onchange')
    location = fields.Char(string='Location', required=True,
                           track_visibility='onchange')
    bank_details = fields.Char(
        string='Bank Details',  track_visibility='onchange')

    currency_id = fields.Many2one(comodel_name='res.currency', required=True,
                                  string='Currency', default=_default_currency, track_visibility='onchange')

    num_word = fields.Char(string="Amount In Words:",
                           compute='_compute_amount_in_word')

    total_amount = fields.Float(
        string='Total amount', compute='_total_amount', readonly=True)

    date_recovery = fields.Date(
        string='Date of Recovery', required=True, track_visibility='onchange')

    @api.multi
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(
                rec.total_amount)) + ' only'

    @api.one
    @api.depends('cash_advance_request_form_line_ids.amount')
    def _total_amount(self):
        for line in self.cash_advance_request_form_line_ids:
            self.total_amount += line.amount

    employee_name = fields.Many2one(
        'res.users', 'Employee Name', readonly=True, track_visibility='onchange')
    employee_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    supervisor_approval = fields.Many2one(
        'res.users', 'Supervisor Name', readonly=True, track_visibility='onchange')
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    audit_approval = fields.Many2one(
        'res.users', 'Auditors Name', readonly=True, track_visibility='onchange')
    audit_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    finance_comments = fields.Char(
        string='Comments', track_visibility='onchange')
    finance_approval = fields.Many2one(
        'res.users', 'Finance Name', readonly=True, track_visibility='onchange')
    finance_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    received_approval = fields.Many2one(
        'res.users', 'Recipients Name',  track_visibility='onchange')
    received_approval_date = fields.Date(
        string='Date', track_visibility='onchange')
    paid = fields.Boolean(string="Paid")
    move_id = fields.Many2one(
        comodel_name="account.move", string="Accounting Entry")
    journal_id = fields.Many2one(
        comodel_name="account.journal", string="Journal")

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
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

    @api.multi
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


class SiteTimeSheet(models.Model):
    _name = 'site.time.sheet'
    _description = 'Site Time Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('opm_approve', 'OPM Approved'),
        ('approve', 'HR Approved'),
        ('reject', 'Reject'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', track_visibility='onchange')

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

    site_time_sheet_line_ids = fields.One2many(
        'site.time.sheet.lines', 'site_time_sheet_id', string="site time sheet lines", copy=True)

    employee_id = fields.Many2one(comodel_name='hr.employee', required=True,
                                  string='Name of Payee', default=_default_employee, track_visibility='onchange')
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', default=_default_department)
    employee_designstion = fields.Char(
        string='Employee Designstion',  track_visibility='onchange')
    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                              ('5', 'May'), ('6', 'June'), ('7',
                                                            'July'), ('8', 'August'),
                              ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                             string='Month', track_visibility='onchange')
    date = fields.Date(string='Date of Submission',
                       required=True, track_visibility='onchange')

    opm_approval = fields.Many2one(
        'res.users', 'OPM Approval', readonly=True, track_visibility='onchange')
    opm_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    hr_approval = fields.Many2one(
        'res.users', 'HR Manager Approval', readonly=True, track_visibility='onchange')
    hr_approval_date = fields.Date(
        string='Date', readonly=True, track_visibility='onchange')

    @api.multi
    def button_submit(self):
        self.write({'state': 'submit'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'project.group_project_manager')
        partner_ids = []
        user_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Site Time Sheet for {} needs your approval".format(
            self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_opm_approval(self):
        self.write({'state': 'opm_approve'})
        self.opm_approval_date = date.today()
        self.opm_approval = self._uid
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'hr.group_hr_manager')
        partner_ids = []
        user_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Site Time Sheet for {} has been approved by OPM".format(
            self.employee_id.name)
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_hr_approval(self):
        self.write({'state': 'approve'})
        self.hr_approval_date = date.today()
        self.hr_approval = self._uid
        subject = "Site Time Sheet for {} has been approved by HR".format(
            self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Site Time Sheet for {} has been rejected".format(
            self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


class SiteTimeSheetLines(models.Model):
    _name = 'site.time.sheet.lines'

    site_time_sheet_id = fields.Many2one(
        comodel_name='site.time.sheet', string='site time sheet')

    date = fields.Date(string='Date', required=True,
                       track_visibility='onchange')
    name = fields.Char(
        string="Brief Description of Activities", required=True,)
    location = fields.Char(string='Location')
    remarks = fields.Char(string='Remarks')


class EmsMonitoring(models.Model):
    _name = 'ems.monitoring'
    _description = 'EMS Monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    kpi_id = fields.Many2one(comodel_name='ems.kpi',
                             string='Key Performance Indicators', required=True)
    uom_id = fields.Many2one(comodel_name='uom.uom',
                             string='Unit of Measurement', required=True)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', required=True)
    target = fields.Float(string='Target', required=True)
    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                              ('5', 'May'), ('6', 'June'), ('7',
                                                            'July'), ('8', 'August'),
                              ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                             string='Month', track_visibility='onchange', required=True)
    remarks = fields.Char(
        string="Remarks (comment on trends and equipment calibration status)")
    date = fields.Date(string='Date', required=True,
                       track_visibility='onchange', default=date.today())


class EmsKpi(models.Model):
    _name = 'ems.kpi'

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string='Active', default=True)


class FumigationSchedule(models.Model):
    _name = 'fumigation.schedule'
    _description = 'Fumigation Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    due_date = fields.Date(string='Due Date of Fumigation', required=True,
                           track_visibility='onchange', default=date.today())
    actual_date = fields.Datetime(
        string='Actual Date of Service', required=True, track_visibility='onchange')
    location = fields.Char(string="Location", required=True)
    remarks = fields.Char(string="Remarks")

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fumigation.schedule') or '/'
        return super(FumigationSchedule, self).create(vals)

    @api.multi
    def action_fumigation_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            # if self.env.context.get('send_rfq', False):
            #    template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase')[1]
            # else:
            template_id = ir_model_data.get_object_reference(
                'topline', 'email_template_edi_fumigation')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'fumigation.schedule',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(
                ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_template(
                    template.lang, ctx['default_model'], ctx['default_res_id'])

        self = self.with_context(lang=lang)
        # if self.state in ['draft', 'sent']:
        #    ctx['model_description'] = _('Request for Quotation')
        # else:
        #    ctx['model_description'] = _('Purchase Order')
        ctx['model_description'] = _('Fumigation Schedule')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class DailyChecklist(models.Model):
    _name = 'daily.checklist'
    _description = 'Daily Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    '''
    livestream = fields.Char(string='LIVESTREAM DISPLAY MONITOR', required=True, track_visibility='onchange')
    #livestream_bool = fields.Boolean(string='LIVESTREAM DISPLAY MONITOR', required=True, track_visibility='onchange')
    accounts_server = fields.Char(string='ACCOUNTS SERVER', required=True, track_visibility='onchange')
    #accounts_server_bool = fields.Boolean(string='ACCOUNTS SERVER', required=True, track_visibility='onchange')
    backup_system = fields.Char(string='BACK-UP SYSTEM', required=True, track_visibility='onchange')
    #backup_system_bool = fields.Boolean(string='BACK-UP SYSTEM', required=True, track_visibility='onchange')
    mtn_radio = fields.Char(string='MTN RADIO', required=True, track_visibility='onchange')
    #mtn_radio_bool = fields.Boolean(string='MTN RADIO', required=True, track_visibility='onchange')
    mtn_rounter_wan = fields.Char(string='MAIN ROUTER (WAN)', required=True, track_visibility='onchange')
    #mtn_rounter_wan_bool = fields.Boolean(string='MAIN ROUTER (WAN)', required=True, track_visibility='onchange')
    wireless_bridge_a = fields.Char(string='WIRELESS BRIDGE A', required=True, track_visibility='onchange')
    #wireless_bridge_a_bool = fields.Boolean(string='WIRELESS BRIDGE A', required=True, track_visibility='onchange')
    wireless_bridge_b = fields.Char(string='WIRELESS BRIDGE B', required=True, track_visibility='onchange')
    #wireless_bridge_b_bool = fields.Boolean(string='WIRELESS BRIDGE B', required=True, track_visibility='onchange')
    intercom = fields.Char(string='INTERCOM', required=True, track_visibility='onchange')
    #intercom_bool = fields.Boolean(string='INTERCOM', required=True, track_visibility='onchange')
    '''

    state = fields.Selection([
        ('new', 'New'),
        ('on', 'Powered On'),
        ('of', 'Powered Off'),
    ], string='Status', readonly=False, index=True, copy=False, default='new', track_visibility='onchange')

    date = fields.Date(string='Date', required=True, default=date.today())

    daily_checklist_power_on_line_ids = fields.One2many(
        'daily.checklist.power.on.line', 'daily_checklist_id', string="Daily Checklist Power On Lines", copy=True)
    daily_checklist_power_off_line_ids = fields.One2many(
        'daily.checklist.power.off.line', 'daily_checklist_id', string="Daily Checklist Power Off Lines", copy=True)

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'daily.checklist') or '/'
        return super(DailyChecklist, self).create(vals)

    @api.one
    def prepare_on_lines(self):
        self.ensure_one()
        sub = self.env['daily.checklist.equipment'].search(
            [('active', '=', True)])
        for check in sub:
            # for line in self.daily_checklist_power_on_line_ids:
            self.daily_checklist_power_on_line_ids.create({
                'daily_checklist_id': self.id,
                'equipment_id': check.id,
                'equipment_on_bool': True,
                'time': datetime.datetime.now().time()
            })
        self.write({'state': 'on'})

    @api.one
    def prepare_off_lines(self):
        self.ensure_one()
        sub = self.env['daily.checklist.equipment'].search(
            [('active', '=', True)])
        for check in sub:
            # for line in self.daily_checklist_power_on_line_ids:
            self.daily_checklist_power_off_line_ids.create({
                'daily_checklist_id': self.id,
                'equipment_id': check.id,
                'equipment_off_bool': True,
                'time': datetime.datetime.now().time()
            })
        self.write({'state': 'of'})


class DailyChecklistPowerOnLines(models.Model):
    _name = 'daily.checklist.power.on.line'
    _description = 'Daily Checklist Power On Lines'

    daily_checklist_id = fields.Many2one(
        comodel_name='daily.checklist', string='Daily Checklist')

    equipment_id = fields.Many2one(
        comodel_name='daily.checklist.equipment', string='Daily Checklist Equipment', required=True)
    equipment_on_bool = fields.Boolean(
        string='On', required=True, track_visibility='onchange')
    equipment_off_bool = fields.Boolean(
        string='Off', required=True, track_visibility='onchange')
    time = fields.Char(string='Time')
    remark = fields.Char(string='Remark', required=False,
                         track_visibility='onchange')


class DailyChecklistPowerOffLines(models.Model):
    _name = 'daily.checklist.power.off.line'
    _description = 'Daily Checklist Power Off Lines'

    daily_checklist_id = fields.Many2one(
        comodel_name='daily.checklist', string='Daily Checklist')

    equipment_id = fields.Many2one(
        comodel_name='daily.checklist.equipment', string='Daily Checklist Equipment', required=True)
    equipment_on_bool = fields.Boolean(
        string='On', required=True, track_visibility='onchange')
    equipment_off_bool = fields.Boolean(
        string='Off', required=True, track_visibility='onchange')
    time = fields.Char(string='Time')
    remark = fields.Char(string='Remark', required=False,
                         track_visibility='onchange')


class DailyChecklistEquipment(models.Model):
    _name = 'daily.checklist.equipment'
    _description = 'Daily Checklist Equipments'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(
        string='Active', default=True, required=False, track_visibility='onchange')
