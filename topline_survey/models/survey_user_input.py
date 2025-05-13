from odoo import models, fields, api

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_department', store=True)

    @api.depends('partner_id')
    def _compute_department(self):
        for record in self:
            employee = self.env['hr.employee'].search([('user_id.partner_id', '=', record.partner_id.id)], limit=1)
            record.department_id = employee.department_id if employee else False

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not res.department_id:
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            if employee:
                res.department_id = employee.department_id
        return res
