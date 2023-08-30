from odoo import models, fields


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    x_studio_asset_no = fields.Char(string="Asset No.")

    def name_get(self):
        res = []

        for asset in self:
            result = asset.name
            if asset.x_studio_asset_no:
                result = str(asset.name) + " " + str(asset.x_studio_asset_no)
            res.append((asset.id, result))
        return res


class AssetMovementFormLine(models.Model):
    _name = "asset.movement.form.line"
    _description = 'Asset Movement Form Line'

    # asset_movement_id = fields.Many2one(
    #     comodel_name='asset.movement.form', string='asset movement form')

    asset_number = fields.Char(string='Asset Number')
    asset_description = fields.Char(string='Asset Description')
    dept = fields.Many2one(comodel_name='hr.department', string='Department')
    location = fields.Char(string='Location')
