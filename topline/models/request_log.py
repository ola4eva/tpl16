from datetime import date
from odoo import models, fields, api


class ActionRequestLog(models.Model):
    _name = "action.request.log"
    _description = 'CORRECTIVE/PREVENTIVE ACTION LOG'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    @api.model
    def _get_default_project(self):
        ctx = self._context
        if ctx.get('active_model') == 'project.project':
            return self.env['project.project'].browse(ctx.get('active_ids')[0]).id

    partner_id = fields.Many2one(
        comodel_name='res.partner', related='project_id.partner_id', string='Customer', readonly=True)

    project_id = fields.Many2one(comodel_name='project.project',
                                 string='Project', readonly=False, default=_get_default_project)

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Owner', default=_default_employee)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', related='employee_id.department_id')

    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Open'),
        ('on_hold', 'On Hold'),
        ('closed', 'Closed'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    action_request_log_line_ids = fields.One2many(
        'action.request.log.line', 'action_request_log_id', string="Action Request Log Line", copy=True)
    date = fields.Date(string='Date', default=date.today())


class ActionRequestLogLine(models.Model):
    _name = "action.request.log.line"
    _description = 'CORRECTIVE/PREVENTIVE ACTION LOG Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    action_request_log_id = fields.Many2one(
        'action.request.log', 'Action Request Log')

    ar_no = fields.Char(string='AR No.')
    initiator_id = fields.Many2one(
        comodel_name='hr.employee', string='Initiator', required=True)
    date_initiated = fields.Date(
        string='Date Initiated', default=date.today(), required=True)
    description_of_problem = fields.Char(
        string='Description of Problem (Nonconformance / Potential Nonconformance)', required=True)
    root_cause = fields.Char(string='Root Cause', required=True)
    action_taken = fields.Char(string='Action Taken')
    date_closed = fields.Date(string='Date Closed')

