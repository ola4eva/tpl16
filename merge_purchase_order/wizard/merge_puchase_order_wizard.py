# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MergePurchaseOrder(models.TransientModel):
    _name = "merge.purchase.order"
    _description = "Merge Purchase Order"
    merge_type = fields.Selection(
        [
            ("new_cancel", "Create new order and cancel all selected purchase orders"),
            ("new_delete", "Create new order and delete all selected purchase orders"),
            (
                "merge_cancel",
                "Merge order on existing selected order and cancel others",
            ),
            (
                "merge_delete",
                "Merge order on existing selected order and delete others",
            ),
        ],
        default="new_cancel",
    )
    purchase_order_id = fields.Many2one("purchase.order", "Purchase Order")

    @api.onchange("merge_type")
    def onchange_merge_type(self):
        res = {}
        for order in self:
            order.purchase_order_id = False
            if order.merge_type in ["merge_cancel", "merge_delete"]:
                purchase_orders = self.env["purchase.order"].browse(
                    self._context.get("active_ids", [])
                )
                res["domain"] = {
                    "purchase_order_id": [
                        ("id", "in", [purchase.id for purchase in purchase_orders])
                    ]
                }
            return res

    def merge_orders(self):
        purchase_orders = self.env["purchase.order"].browse(
            self._context.get("active_ids", [])
        )
        partner = purchase_orders[0].partner_id.id
        self.merge_validation(purchase_orders, partner)
        if self.merge_type in ["new_cancel", "new_delete"]:
            new_po = (
                self.env["purchase.order"]
                .with_context(
                    {"trigger_onchange": True, "onchange_fields_to_trigger": [partner]}
                )
                .create({"partner_id": partner})
            )
            default = {"order_id": new_po.id}
            for order in purchase_orders:
                self.manage_purchase_order_line(order, new_po, default)
            for order in purchase_orders:
                order.sudo().button_cancel()
                if self.merge_type == "new_delete":
                    order.sudo().unlink()
        else:
            new_po = self.purchase_order_id
            default = {"order_id": self.purchase_order_id.id}
            for order in purchase_orders:
                if order == new_po:
                    continue
                self.manage_purchase_order_line(order, new_po, default)
            for order in purchase_orders:
                if order != new_po:
                    order.sudo().button_cancel()
                    if self.merge_type == "merge_delete":
                        order.sudo().unlink()

    def manage_purchase_order_line(self, existing_order, new_order, default):
        for line in existing_order.order_line:
            existing_po_line = False
            if new_order.order_line:
                for new_line in new_order.order_line:
                    if (
                        line.product_id == new_line.product_id
                        and line.price_unit == new_line.price_unit
                    ):
                        existing_po_line = new_line
                        break
            if existing_po_line:
                existing_po_line.product_qty += line.product_qty
                po_taxes = [tax.id for tax in existing_po_line.taxes_id]
                [po_taxes.append(tax.id) for tax in line.taxes_id]
                existing_po_line.taxes_id = [(6, 0, po_taxes)]
            else:
                line.copy(default=default)

    def merge_validation(self, purchase_orders, partner):
        if len(self._context.get("active_ids", [])) < 2:
            raise UserError(
                _(
                    "Please select at least two purchase orders to perform the Merge "
                    "Operation."
                )
            )
        if any(order.state != "draft" for order in purchase_orders):
            raise UserError(
                _(
                    "Please select Purchase orders which are in RFQ state to perform "
                    "the Merge Operation."
                )
            )
        if any(order.partner_id.id != partner for order in purchase_orders):
            raise UserError(
                _(
                    "Please select Purchase orders whose Vendors are same to perform "
                    "the Merge Operation."
                )
            )
