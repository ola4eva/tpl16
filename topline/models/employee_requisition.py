# -*- coding: utf-8 -*-

from odoo import fields, models, _


class EmployeeRequisitionForm(models.Model):
    _name = "employee.requisition.form"
    _description = 'Employee Requisition Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_department(self):
        user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user.department_id.id

    # this method is to search the hr.employee and return the user id of the person clicking the form atm
    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    state = fields.Selection([
        ('draft', 'New'),
        ('submit', 'Submitted'),
        ('line_manager', 'Supervisor'),
        ('hr_manager', 'HR Manager'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)

    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', default=_default_department)
    job_id = fields.Many2one(comodel_name='hr.job', string='Job Title')
    no_personnel_required = fields.Integer(string='No. of Personnel Required')
    existing_staff_present_in_category = fields.Integer(
        string='Existing Staff at present in this category')
    location = fields.Char(string='Location (mention details)')
    type_of_appointment = fields.Char(string='Type of Appointment')
    temporary_duration = fields.Char(
        string='If contract/temporary, state duration')
    qualification_required = fields.Char(
        string='Educational/Professional Qualification Required')
    skill_required = fields.Char(string='Skills Required')
    experience_required = fields.Char(string='Experience Required')
    job_description = fields.Char(string='Job Description')
    resource_required_date = fields.Date(
        string='Date by which Resource is Required')
    vacancy_cause = fields.Char(
        string='Vacancy caused due to (Resignation / Work Load / Additional Assignments)')
    vacancy_filled_internally = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Can vacancy be filled through internal transfers/promotion etc?')
    benefits_to_accrue = fields.Char(
        string='Benefits to Accrue on Additional Appointment')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='PROPOSED BY:', default=_default_employee)
    line_manager_approval = fields.Many2one(
        comodel_name='res.users', string='Name of Approving Authority')

    suggestion_for_replacement = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Suggestion for replacement if possible')
    name_of_person = fields.Char(
        string='Name of Person you intend to replace with')
    statement_of_justification = fields.Char(
        string='Statement of Justification for Internal / External Recruitment :')
    salary_range = fields.Float(string='Range of Salary ')
    when_position_filled = fields.Date(
        string='When the position can be filled up')
    remarks = fields.Char(string='Remarks')

    hr_manager_approval = fields.Many2one(
        comodel_name='res.users', string='(Approval Of HEAD – HR)')

    def action_submit(self):
        self.state = "submit"

    def action_line_manager_approve(self):
        self.state = "line_manager"

    def action_hr_manager_approve(self):
        self.state = "hr_manager"

    def action_final_approve(self):
        if self.job_id:
            if self.job_id.state != "recruit":
                self.job_id.state = "recruit"
            self.job_id.write({
                "no_of_recruitment": self.no_personnel_required,
                "department_id": self.department_id.id,
                "hr_responsible_id": self.env.user.id,
                "user_id": self.env.user.id,
                "description": self.job_description
            })
        return self.write({'state': "approve"})

    def open_job_posting(self):
        action = self.env.ref('hr.action_hr_job').read()[0]
        action['context'] = dict(self.env.context)
        action['views'] = [(self.env.ref('hr.view_hr_job_form').id, 'form')]
        action['res_id'] = self.job_id.id
        return action
