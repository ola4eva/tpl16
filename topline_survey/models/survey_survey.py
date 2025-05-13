from odoo import models, fields

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    def _get_default_department(self):
        return self.env.user.department_id.id if self.env.user.department_id else False

    department_id = fields.Many2one('hr.department', string='Department', default=_get_default_department)
