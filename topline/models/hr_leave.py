# -*- coding: utf-8 -*-

from odoo import fields, models, _


class HolidaysRequest(models.Model):
    _name = "hr.leave"
    _inherit = "hr.leave"

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
        help="The status is set to 'To Submit', when a leave request is created." +
        "\nThe status is 'To Approve', when leave request is confirmed by user." +
        "\nThe status is 'Refused', when leave request is refused by manager." +
        "\nThe status is 'Approved', when leave request is approved by manager.")


class HolidaysType(models.Model):
    _name = "hr.leave.type"
    _inherit = "hr.leave.type"

    # TODO: remove me in master
    def _inverse_validation_type(self):
        for holiday_type in self:
            if holiday_type.double_validation == True:
                holiday_type.validation_type = 'both'
            else:
                # IF to preserve the information (hr or manager)
                if holiday_type.validation_type == 'both':
                    holiday_type.validation_type = 'manager'
