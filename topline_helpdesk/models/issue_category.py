from odoo import models, fields


class issueCategory(models.Model):
    _name = "topline_helpdesk.issue.category"
    _description = "Issue Category"

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
