# -*- coding: utf-8 -*-
from datetime import datetime
from urllib.parse import urlencode
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class InterDepartmentalRequest(models.Model):

    _name = 'inter_departmental.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Inter-departmental Request'
    _order = 'create_date desc'

    def _get_default_user_id(self):
        return self.env.uid

    def _get_default_employee(self):
        user_id = self._get_default_user_id()
        employee = self.env['hr.employee'].sudo().search(
            [('user_id', '=', user_id)])
        return employee

    def _get_default_source_department_id(self):
        department_id = False
        employee = self._get_default_employee()
        return employee and employee.department_id and employee.department_id.id or department_id

    name = fields.Char(string="Name", required=True,
                       readonly=True, default="/")
    request_details = fields.Text(string='Request Details', readonly=True, states={'draft': [('readonly', False)]})
    user_id = fields.Many2one(comodel_name="res.users",
                              string="Requester", default=_get_default_user_id, readonly=True, states={'draft': [('readonly', False)]})
    src_department_id = fields.Many2one(
        comodel_name="hr.department", string="Requesting Department", default=_get_default_source_department_id, readonly=True, states={'draft': [('readonly', False)]})
    dest_department_id = fields.Many2one(
        comodel_name="hr.department", string="Destination Department", readonly=True, states={'draft': [('readonly', False)]})
    responsible_user_id = fields.Many2one(
        comodel_name="res.users", string="Responsible", readonly=True, states={'draft': [('readonly', False)]})
    date_deadline = fields.Datetime('Deadline', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    date_requested = fields.Datetime('Request Date', readonly=True, copy=False)
    date_resolved = fields.Datetime('Resolution Date', readonly=True, copy=False)
    date_confirmed = fields.Datetime('Confirmation Date', readonly=True, copy=False)
    resolution_timeline = fields.Char(
        string="Resolution Timeline", readonly=True, copy=False)
    resolution_delay = fields.Char(
        string="Resolution Delay", readonly=True, compute="_compute_resolution_delay", copy=False)
    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('process', 'Processing'),
        ('complete', 'Completed'),
        ('confirm', 'Confirmed By Requester'),
        ('cancel', 'Cancelled'),
    ], string='State', default="draft", readonly=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code(
                "interdepartmental.request")
        return super().create(vals)

    def action_submit(self):
        for record in self:
            try:
                email_template = self.env.ref(
                    "topline_inter_departmental_request.email_submit_request_to_responsible")
                email_template.send_mail(record.id, force_send=True)
            except:
                pass
            return record.update({
                'state': "submit",
                'date_requested': datetime.now(),
            })

    def action_process(self):
        for record in self:
            try:
                email_template = self.env.ref(
                    "topline_inter_departmental_request.email_request_responsible_set_to_progress")
                email_template.send_mail(record.id, force_send=True)
            except:
                pass
            if record.env.user != record.responsible_user_id:
                raise UserError("Only the responsible is allowed to do this!")
            record.state = "process"

    def action_complete(self):
        for record in self:
            try:
                email_template = self.env.ref(
                    "topline_inter_departmental_request.email_responsible_complete_request")
                email_template.send_mail(record.id, force_send=True)
            except:
                pass
            if record.env.user != record.responsible_user_id:
                raise UserError("Only the responsible is allowed to do this!")
            record.update({
                'state': "complete",
                'date_resolved': datetime.now(),
            })
            return record._compute_resolution_timeline()

    def action_confirm(self):
        for record in self:
            email_template = False
            try:
                email_template = self.env.ref(
                    "topline_inter_departmental_request.email_user_confirm_completion")
                email_template.send_mail(record.id, force_send=True)
            except:
                pass
            if record.env.user != record.user_id:
                raise UserError(
                    "Only the requester can confirm successful completion!")
            return record.update({
                'state': "confirm",
                'date_confirmed': datetime.now()
            })

    def action_dispute(self):
        for record in self:
            try:
                email_template = self.env.ref(
                    "topline_inter_departmental_request.email_user_dispute_completion")
                email_template.send_mail(record.id, force_send=True)
            except:
                pass
            if record.env.user != record.user_id:
                raise UserError(
                    "Only the requester can confirm successful completion!")
            record.state = "dispute"

    def action_cancel(self):
        if self.env.user_id != self.user_id:
            raise UserError(
                "You can't cancel requests that were not created by you")
        self.state = "cancel"

    def get_base_url(self):
        return self.sudo().env['ir.config_parameter'].get_param('web.base.url')

    def get_record_url(self):
        return self._get_record_url()

    def _get_record_url(self):
        base_url = self.get_base_url()
        for record in self:
            params = {
                "id": record.id,
                "cids": record.id,
                "action": int(self.sudo().env.ref("topline_inter_departmental_request.inter_departmental_request_action")),
                "model": self._name,
                "menu_id": int(self.sudo().env.ref("topline_inter_departmental_request.menu_root")),
                "view_type": "form",
            }
            url = f"{base_url}/web#{urlencode(params)}"
            self.url = url
            return url

    @api.constrains('user_id', 'responsible_user_id')
    def _check_user_not_responsible(self):
        for record in self:
            if record.user_id == record.responsible_user_id:
                raise UserError(
                    "Requester and Responsible user cannot be the same")

    @api.constrains('src_department_id', 'dest_department_id')
    def _check_source_department_not_destination_department(self):
        for record in self:
            if record.src_department_id == record.dest_department_id:
                raise UserError(
                    "Source and destination departments cannot be equal")

    def _compute_resolution_delay(self):
        for record in self:
            resolution_delay = ""
            if not record.date_resolved:
                record.resolution_delay = ""
            else:
                if record.date_resolved > record.date_deadline:
                    time_diff = datetime.timestamp(
                        record.date_resolved) - datetime.timestamp(record.date_deadline)
                    minute_interim, secs = divmod(time_diff, 60)
                    hours, minutes = divmod(minute_interim, 60)
                    resolution_delay = f"{round(hours, 2)} hours {round(minutes, 2)} minutes {round(secs, 2)} seconds"
            record.resolution_delay = resolution_delay

    def _compute_resolution_timeline(self):
        for record in self:
            if not record.date_resolved:
                record.resolution_timeline = ""
            else:
                time_diff = datetime.timestamp(
                    record.date_resolved) - datetime.timestamp(record.date_requested)
                minute_interim, secs = divmod(time_diff, 60)
                hours, minutes = divmod(minute_interim, 60)
                record.resolution_timeline = f"{round(hours, 2)} hours {round(minutes, 2)} minutes {round(secs, 2)} seconds"
