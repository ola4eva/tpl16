# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Task(models.Model):
    _inherit = "project.task"

    task_done = fields.Boolean(string='task Completed', copy=False)
    task_team_ids = fields.Many2many(comodel_name='hr.employee', string='Team')

    @api.depends('effective_hours', 'subtask_effective_hours', 'planned_hours')
    def _compute_progress_hours(self):
        for task in self:
            if (task.planned_hours > 0.0):
                task_total_hours = task.effective_hours + task.subtask_effective_hours
                if task_total_hours > task.planned_hours and task.remaining_hours > 0:
                    task.progress = 100
                elif task.remaining_hours < 0:
                    task.progress = 80
                else:
                    task.progress = round(
                        100.0 * task_total_hours / task.planned_hours, 2)

    @api.onchange('progress')
    def _onchange_progress(self):
        if self.remaining_hours < 0:
            self.progress = 80

    
    def button_task_complete(self):
        if any(task for task in self.timesheet_ids):
            self.progress = 100
            self.task_done = True
            # self.stage_id.name = "DONE"
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Go, go, go! Congrats on your task completion.',
                    'img_url': '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            warning_mess = {
                'title': _('No Task(s) Recorded!'),
                'message': _("You have attempted to mark a task as done without any timesheet lines "
                             "please do specify some timesheet line(s)."),
            }
            user_warning = _(
                'You have attempted to mark a task as done without any timesheet recording(s), please do specify some timesheet line(s).')
            # return {'warning': warning_mess}
            raise UserError(user_warning)

