# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from odoo.exceptions import Warning
from odoo import models, _


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    def get_adjustment(self, code, payslip_id, emp_id, date_from, date_to=None):
        if date_to is None:
            date_to = datetime.now()
        self._cr.execute("""
            SELECT o.id, o.amount from adjustment_type_line AS o LEFT JOIN payroll_adjustment AS a 
            ON a.id=o.adjustment_line_id WHERE o.applied IS FALSE AND o.employee_id=%s 
            AND a.code=%s AND a.state = %s AND o.start_date >= %s AND o.start_date <= %s """,
            (emp_id, code, 'running', date_from, date_to)
        )
        res = self._cr.fetchone()
        if res:
            adjustment_line = self.env['adjustment.type.line'].browse(res[0])
            adjustment_line.payslip_id = payslip_id
            return res and res[1] or 0.0
        else:
            return 0.0

