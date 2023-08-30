# -*- coding: utf-8 -*-

from urllib.parse import urlencode
from odoo import models, fields, api
from odoo.exceptions import UserError

SELECTION_APPRAISAL = [
    ("draft", "New"),
    ("sent", "Sent To Employee"),
    ("manager", "Manager To Assess"),
    ("done", "Manager Assessed"),
]


class EmployeeAppraisal(models.Model):
    _name = "employee_appraisal.employee_appraisal"
    _inherit = ["mail.activity.mixin", "mail.thread"]
    _description = "Employee Performance Assessment"

    def _get_default_user_id(self):
        return self.env.uid

    name = fields.Char(
        string="Name",
        required=True,
        readonly=True,
        default="/",
        states={"draft": [("readonly", False)]},
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        required=False,
        related="employee_id.department_id",
    )
    job_id = fields.Many2one(
        "hr.job",
        string="Job Title",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    template_id = fields.Many2one(
        'employee_appraisal.appraisal.template', string='Template')
    employee_number = fields.Char('Employee ID Number')
    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')
    overall_score = fields.Float(
        'Total Score', compute="_compute_overall_score")
    overall_self_score = fields.Float(
        'Total Self Score', compute="_compute_overall_self_score")
    parent_id = fields.Many2one(
        "hr.employee",
        string="Supervisor",
        required=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    user_id = fields.Many2one(
        "res.users", string="Responsible", default=_get_default_user_id
    )
    state = fields.Selection(
        SELECTION_APPRAISAL,
        string="State",
        default="draft",
        tracking=True,
    )
    question_ids = fields.One2many(
        "employee_appraisal.question", "appraisal_id", string="Evaluations"
    )
    url = fields.Char("url", compute="_get_record_url")
    active = fields.Boolean('Active?', default=True)
    manager_comment = fields.Text('Manager\'s Comment')
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    key_achievements = fields.Text('Key Achievements', help="""To Be Completed by Jobholder (Document below key contributions/strength areas relative to the agreed goals/targets)
    """)
    key_strengths = fields.Char(
        'Key Strengths', help="""To Be Completed by Supervisor (Document below key contributions/strength areas of the jobholder relative to the agreed goals/targets)""")
    areas_of_improvement = fields.Text(
        'Areas of Improvement', help="""To Be Completed by Supervisor (Document below key areas for improvement for the jobholder relative to the agreed goals/targets)""")
    development_activities = fields.Text('Proposed Development Activities', help="""
    To Be Completed by Supervisor (Document below the key areas where performance improvement is required relative to the defined goals)
    """)
    concurrent_reviewer_comment = fields.Text("Concurrent Reviewer's Comment")
    performance_score = fields.Float('Performance Score', compute="_compute_performance_score")
    behavioural_score = fields.Float('Behavioural Score', compute="_compute_behavioural_score")
    total_score = fields.Float(string='Total Score')
    overall_rating = fields.Char(
        'Overall Rating / Category', compute="_compute_overall_rating")
    accept = fields.Selection([
        ('accept', 'I Accept'),
        ('reject', 'I Reject')
    ], string='Accept/Reject', readonly=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].sudo(
        ).next_by_code('employee.appraisal')
        return super().create(vals)

    def _compute_overall_rating(self):
        for record in self:
            record.overall_rating = record.performance_score + record.behavioural_score

    def _compute_overall_score(self):
        for record in self:
            total = 0
            for question in record.question_ids.filtered(lambda qid: qid.is_section is False and qid.is_subsection is False):
                total += question.score_total
            overall_score = total
            record.overall_score = overall_score

    def _compute_overall_self_score(self):
        for record in self:
            total = 0
            for question in record.question_ids.filtered(lambda qid: qid.is_section is False and qid.is_subsection is False):
                total += question._compute_total_self_score()
            overall_score = total
            record.overall_self_score = overall_score

    @api.depends("question_ids.score_total")
    def _compute_performance_score(self):
        for record in self:
            performance_code = record.template_id.code_competence_section
            performance_score = 0
            for question in record.question_ids.filtered(lambda question: not question.is_section and not question.is_subsection and question.section_code == performance_code):
                performance_score += question.score_total
            record.performance_score = performance_score

    @api.depends("question_ids.score_total")
    def _compute_behavioural_score(self):
        for record in self:
            behavioural_code = record.template_id.code_behavioural_section
            behavioural_score = 0
            for question in record.question_ids.filtered(lambda question: not question.is_section and not question.is_subsection and question.section_code == behavioural_code):
                behavioural_score += question.score_total
            record.behavioural_score = behavioural_score

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        value = {"value": {}}
        if self.employee_id:
            department_id = (
                self.employee_id.department_id and self.employee_id.department_id.id
            )
            job_id = self.employee_id.job_id and self.employee_id.job_id.id
            parent_id = self.employee_id.parent_id and self.employee_id.parent_id.id
            value["value"].update(
                {
                    "department_id": department_id,
                    "job_id": job_id,
                    "parent_id": parent_id,
                }
            )
        return value

    def action_send_to_employee(self):
        # send an email to employee
        template = self.env.ref(
            "topline_employee_appraisal.employee_appraisal_request_email_to_employee")
        template.send_mail(self.id, force_send=True)
        self.state = "sent"

    def action_send_to_manager(self):
        # send an email to manager
        template = self.env.ref(
            "topline_employee_appraisal.employee_appraisal_request_email_to_employee_manager"
        )
        template.send_mail(self.id, force_send=True)
        self.state = "manager"

    def action_complete_assessment(self):
        # send notification to hr manager
        template = self.env.ref(
            "topline_employee_appraisal.employee_appraisal_completion_email_to_hr")
        template.send_mail(self.id, force_send=True)
        self.state = "done"

    def _get_record_url(self):
        base_url = self.get_base_url()
        params = {
            "id": self.id,
            "cids": self.id,
            "action": int(self.env.ref("topline_employee_appraisal.employee_appraisal_action")),
            "model": self._name,
            "menu_id": int(self.env.ref("topline_employee_appraisal.employee_appraisal_heading_menu")),
            "view_type": "form",
        }
        url = f"{base_url}/web#{urlencode(params)}"
        self.url = url

    def unlink(self):
        for record in self:
            if record.state not in "draft":
                raise UserError("You cannot delete records not in draft!")
        return super().unlink()

    def accept_appraisal_score(self):
        if not self.env.user == self.employee_id.user_id:
            raise UserError(
                "You are not allowed to accept on behalf of another appraisee!")
        self.write({"accept": "accept"})

    def reject_appraisal_score(self):
        if not self.env.user == self.employee_id.user_id:
            raise UserError(
                "You are not allowed to reject on behalf of another appraisee!")
        self.accept = "reject"

    @api.onchange("template_id")
    def _onchange_template_id(self):
        if self.template_id:
            self.question_ids.unlink()
            Question = self.env["employee_appraisal.question"].sudo()
            new_questions = self.question_ids
            for question in self.template_id.question_ids:
                appraisal_question = Question.create(
                    {
                        "name": question.name,
                        "weight": question.weight,
                        "is_section": question.is_section,
                        "is_subsection": question.is_subsection,
                        "code": question.code,
                        "section_code": question.section_code,
                    }
                )
                new_questions += appraisal_question
            self.question_ids = new_questions


class EmployeeAppraisalQuestion(models.Model):
    _name = "employee_appraisal.question"
    _description = "Employee Appraisal Question"

    SCORE_SELECTION = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ]
    name = fields.Char(
        string="Assessment",
        #    readonly=True,
        #    states={'draft': [('readonly', False)]}
    )
    weight = fields.Float(
        "Weight",
        #   readonly=True, states={
        #   'draft': [('readonly', False)]}
    )
    appraisal_id = fields.Many2one(
        "employee_appraisal.employee_appraisal", string="Appraisal", ondelete="cascade")
    is_section = fields.Boolean("Is Section")
    is_subsection = fields.Boolean("Is Subsection")
    code = fields.Char('Code', readonly=True)
    section_code = fields.Char('Section Code', readonly=True)
    state = fields.Selection(related="appraisal_id.state", default="draft")
    score_self = fields.Selection(
        selection=SCORE_SELECTION, string='Self Score',
        #   readonly=True,
        #   states={
        #   'manager': [('readonly', False)]}
    )
    score_supervisor = fields.Selection(
        selection=SCORE_SELECTION, string='Supervisor Score',
        # readonly=True,
        # states={'sent': [('readonly', False)]}
    )
    score_total = fields.Integer(
        string="Total Score", compute="_compute_total_score")
    comment_self = fields.Char(
        'Comment (Self)',
        # readonly=True,
        # states={
        # 'sent': [('readonly', False)]}
    )
    comment_supervisor = fields.Char(
        'Comment (Supervisor)',
        # readonly=True, states={
        # 'sent': [('readonly', False)]}
    )

    @api.depends("weight", "score_supervisor")
    def _compute_total_score(self):
        for line in self:
            total_score = 0
            if line.weight and line.score_supervisor:
                total_score = line.weight * int(line.score_supervisor) / 5
            line.score_total = total_score

    @api.depends("weight", "score_self")
    def _compute_total_self_score(self):
        for line in self:
            total_score = 0
            if line.weight and line.score_supervisor:
                total_score = line.weight * int(line.score_supervisor) / 5
            return total_score
