# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api
import datetime

class UserAudit(models.Model):
    _name = "sh.user.audit.log"
    _description = "User Audit Logs"
    _order = 'id desc'

    object = fields.Many2one('ir.model', string="Object")
    record_id = fields.Integer(string="Record ID")
    name = fields.Char(string="Reference", readonly=True)
    user = fields.Many2one('res.users', string="User")
    type = fields.Selection([
        ("read", "Read"),
        ("write", "Write"),
        ("create", "Create"),
        ("delete", "Delete"),
    ], string='Type' )
    modify_date = fields.Datetime(string="Date")
    updated_field = fields.Many2one('ir.model.fields', string="Update Field")
    value_updated = fields.Char("Updated Value")
    old_value = fields.Char("Old Values")
    # view_type = fields.Char('View', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.update(
                {"name": self.env["ir.sequence"].next_by_code("name.entry")})
        return super(UserAudit, self).create(vals_list)
