# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError


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

    def unlink(self):
        for request in self:
            if request.stage_id != self._default_stage():
                raise UserError(
                    "You can only delete requests in %s stage!!!" % self._default_stage().name)
            return super(MaintenanceRequest, self).unlink()

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

    def button_approval_maintenance_manager(self):
        subject = "Maintenance Request {} has been approved by Maintenance Manager".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_qaqc()

    def button_approval_qaqc_manager(self):
        subject = "Maintenance Request {} has been approved by QA/QC Manager".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_store()

    def button_approval_store_manager(self):
        self.stage_id = 2
        subject = "Maintenance Request {} has been approved by Store Manager".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_repair(self):
        self.stage_id = 3
        subject = "Maintenance Request {} has been Rejected".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_scrap(self):
        self.stage_id = 4
        subject = "Maintenance Request {} has been Scrapped".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_reject(self):
        self.stage_id = 8
        subject = "Maintenance Request {} has been Rejected".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)


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
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    # asset_id = fields.Many2one(
    #     comodel_name='account.asset.asset', string='Asset(s):')

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
        'res.users', 'Supervisor Name', readonly=True, tracking=True)
    supervisor_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

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
        'res.users', 'Manager Name', readonly=True, tracking=True)
    manager_approval_date = fields.Date(
        string='Date', readonly=True, tracking=True)

    ref = fields.Char('Order Reference', readonly=False,
                      required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('ref', 'New') == 'New':
            vals['ref'] = self.env['ir.sequence'].next_by_code(
                'maintenance.request.failure.report.sheet') or '/'
        return super(MaintenanceRequestAndFailureReportSheet, self).create(vals)

    # @api.onchange('asset_id')
    # def _update_asset_fields(self):
    #     self.name = self.asset_id.name
    #     self.asset_no = self.asset_id.x_studio_asset_no

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

    def action_reject(self):
        self.write({'state': 'reject'})
        subject = "Maintenance Request And Failure Report Sheet {} has been Rejected".format(
            self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
