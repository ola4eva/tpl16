import logging
from datetime import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    date_created = fields.Datetime(string="Submitted On", readonly=True)
    date_resolved = fields.Datetime("Resolution On", readonly=True)
    resolution_time = fields.Char("Resolution Time", compute="_compute_resolution_time")
    submitted = fields.Boolean("Submitted")

    @api.model_create_multi
    def create(self, vals_list):
        """Override the create method to set the date_created field."""
        for vals in vals_list:
            if not vals.get("date_created"):
                vals["date_created"] = fields.Datetime.now()
        return super().create(vals_list)

    def _creation_subtype(self):
        return None

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
        template = self.env.ref("topline_helpdesk.email_template_ticket_submitted")
        for record in self:
            try:
                _logger.info(f"Sending email to {self.team_id.message_partner_ids}")
                _logger.info(
                    f"Sending email to {','.join(recipient.email_formatted for recipient in self.team_id.message_partner_ids) }"
                )
                template.with_context(
                    recipients=self.team_id.message_partner_ids.mapped(
                        "email_formatted"
                    )
                ).send_mail(record.id, force_send=True)
            except Exception as e:
                _logger.error("Failed to send email: %s", e)
            else:
                record.submitted = True
                if not record.date_created:
                    record.date_created = fields.Datetime.now()

    def write(self, vals):
        super().write(vals)
        if vals.get("stage_id"):
            if (
                self.env["helpdesk.stage"].browse(vals.get("stage_id")).fold
                and not self.date_resolved
            ):
                self.action_mark_close()

    def action_reset(self):
        self.date_created = False
        self.date_resolved = False
        self.resolution_time = False
        self.submitted = False
        self.stage_id = False
