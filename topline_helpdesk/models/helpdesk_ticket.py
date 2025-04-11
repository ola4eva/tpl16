import logging
from datetime import datetime
from odoo import models, fields

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    date_created = fields.Datetime(string="Submitted On", readonly=True)
    date_resolved = fields.Datetime("Resolution On", readonly=True)
    resolution_time = fields.Char("Resolution Time", compute="_compute_resolution_time")
    submitted = fields.Boolean("Submitted")
    issue_category_id = fields.Many2one(
        comodel_name="topline_helpdesk.issue.category", string="Issue Category"
    )

    def action_mark_close(self):
        """Mark the ticket as closed."""
        for rec in self:
            rec.date_resolved = fields.Datetime.now()
            return self._compute_resolution_time()

    def _compute_resolution_time(self):
        """Compute the resolution time for each ticket."""
        for record in self:
            resolution_time = ""
            if not record.date_resolved:
                record.resolution_time = resolution_time
                continue
            if not record.date_created:
                record.resolution_time = resolution_time
                continue
            time_diff = datetime.timestamp(self.date_resolved) - datetime.timestamp(
                record.date_created
            )
            minute_interim, secs = divmod(time_diff, 60)
            hours, minutes = divmod(minute_interim, 60)
            resolution_time = f"{round(hours, 2)} hours {round(minutes, 2)} minutes {round(secs, 2)} seconds"
            record.resolution_time = resolution_time

    def action_submit(self):
        """Submit the ticket for review.

        This method is called when the user clicks the "Submit" button
        on the ticket form. It performs the following actions:
        1. Sends a notification to the responsible user.
        2. Updates the ticket status to "Submitted".
        """
        if self.submitted:
            not self.submitted
        template = self.env.ref("helpdesk.new_ticket_request_email_template")
        for record in self:
            try:
                template.send_mail(record.id, force_send=True)
            except Exception as e:
                _logger.error("Failed to send email: %s", e)
            else:
                record.submitted = True
                if not record.date_created:
                    record.date_created = fields.Datetime.now()

    def write(self, vals):
        super().write(vals)
        for record in self:
            if vals.get("stage_id"):
                if (
                    self.env["helpdesk.stage"].browse(vals.get("stage_id")).fold
                    and not record.date_resolved
                ):
                    record.action_mark_close()

    def action_reset(self):
        "Reset ticket to draft state"
        self.date_created = False
        self.date_resolved = False
        self.resolution_time = False
        self.submitted = False
        self.stage_id = False
