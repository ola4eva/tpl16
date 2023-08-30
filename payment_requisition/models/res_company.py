from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"
    
    md_proxy_approval_limit = fields.Float(string='Amount')
