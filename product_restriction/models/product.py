# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import UserError


class ProductTemplateRestriction(models.Model):
    _inherit = 'product.template'

    # Come back to the string quotes problem

    # @api.model_create_multi
    # def create(self, vals_list):
    #     # if product with same name exists raise an error
    #     for vals in vals_list:
    #         if 'name' in vals:
    #             name = str(vals.get("name"))
    #             print("^^^^^^^^^^^^^^^^^^6", name)
    #             Query = """
    #                 SELECT COALESCE(name->>'en_US') AS name from product_template where name = '{"en_US": %s}'
    #             """
    #             self.env.cr.execute(Query, (name,))
    #             existing_products = self.env.cr.fetchall()
    #             if existing_products:
    #                 raise UserError("A similar product exists!!!")
    #     res_ids = super(ProductTemplateRestriction, self).create(vals_list)
    #     return res_ids