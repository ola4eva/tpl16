from odoo import models, fields

class FleetVehicleCost(models.Model):
    _name = 'fleet.vehicle.cost'
    _inherit = 'fleet.vehicle.cost'

    vehicle_return_date = fields.Date(string='Return Date')
    vehicle_date_of_standby = fields.Date(string='Date of Standby')
    reason_for_standby = fields.Char(
        string='Reason for standby', help="reason for delay. When return date is due and vehicle is yet to be returned")
