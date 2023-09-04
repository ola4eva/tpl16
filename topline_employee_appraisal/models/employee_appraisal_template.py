from odoo import models, fields, api
from odoo.exceptions import UserError


class EmployeeAppraisalTemplate(models.Model):
    _name = "employee_appraisal.appraisal.template"
    _inherit = ['mail.thread', "mail.activity.mixin"]
    _description = "Appraisal Template"

    name = fields.Char(string="Name", tracking=True, readonly=True, states={
                       'draft': [('readonly', False)]})
    user_id = fields.Many2one(
        "res.users", string="User", readonly=True, default=lambda self: self.env.uid)
    department_id = fields.Many2one(
        'hr.department', string='Department', tracking=True, readonly=True, states={'draft': [('readonly', False)]})

    question_ids = fields.One2many(
        "employee_appraisal.appraisal.template.question", "template_id", string="Evaluations", readonly=True, states={'draft': [('readonly', False)]}
    )
    state = fields.Selection(
        [
            ("draft", "New"),
            ("open", "To Approve"),
            ("approve", "Approved"),
        ],
        string="State",
        default="draft",
        required=True,
        tracking=True,
    )
    active = fields.Boolean('Active?', default=True)
    code_behavioural_section = fields.Char('Behavioural Section Code', readonly=True, states={'draft': [('readonly', False)]})
    code_competence_section = fields.Char('Competence Section Code', readonly=True, states={'draft': [('readonly', False)]})

    def action_submit(self):
        self.state = "open"

    def action_approve(self):
        self.state = "approve"

    def unlink(self):
        for record in self:
            if record.state not in "draft":
                raise UserError("You cannot delete records not in draft!")
        return super().unlink()


class EmployeeAppraisalQuestion(models.Model):
    _name = "employee_appraisal.appraisal.template.question"
    _description = "Employee Appraisal Template Question"

    name = fields.Char(string="Key Performance Indicators", required=True)
    weight = fields.Float("Weight")
    is_section = fields.Boolean(string="Is Section")
    is_subsection = fields.Boolean(string="Is Subsection")
    template_id = fields.Many2one(
        "employee_appraisal.appraisal.template", string="Template", required=True)
    code = fields.Char('Code')
    section_code = fields.Char('Parent Code')

    @api.constrains('weight')
    def _constrains_weight(self):
        for record in self:
            if not (record.is_section or record.is_subsection):
                if record.weight <= 0:
                    raise UserError("Weight must be strictly positive")

    @api.constrains('target')
    def _constrains_target(self):
        for record in self:
            if not (record.is_section or record.is_subsection):
                if record.target <= 0:
                    raise UserError("Target must be strictly positive")
                if record.target > 100:
                    raise UserError("Target cannot be greater than 100%")