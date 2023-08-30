# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import UserError


class ProductTemplateRestriction(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, values):
        # if product with same name exists raise an error
        if 'name' in values:
            name = values.get("name")
            Query = """
                select * from product_template where name ilike %s  
            """
            self.env.cr.execute(Query, (name,))
            existing_products = self.env.cr.fetchall()
            if existing_products:
                raise UserError("A similar product exists!!!")
        res = super(ProductTemplateRestriction, self).create(values)
        return res