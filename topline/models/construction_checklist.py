# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _


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
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

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
        'res.users', 'Supervisor Name', readonly=True, tracking=True)
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)
    manager_approval = fields.Many2one(
        'res.users', 'Manager Name', readonly=True, tracking=True)
    manager_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)
    store_approval = fields.Many2one(
        'res.users', 'Store Personnel Name', readonly=True, tracking=True)
    store_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)
    qa_qc_approval = fields.Many2one(
        'res.users', 'QA/QC Personnel Name', readonly=True, tracking=True)
    qa_qc_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

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
