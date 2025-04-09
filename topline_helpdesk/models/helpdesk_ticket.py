from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    date_created = fields.Date(string="Creation Date", readonly=True)
    date_resolved = fields.Date("Resolution Date", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        context = dict(self.env.context)
        context.update(
            {
                "mail_create_nolog": True,
                "mail_auto_subscribe_no_notify": True,  # don't notify followers
                "mail_notify_force_send": False,  # suppress sending mails
            }
        )

        # Optional: update vals if needed
        for vals in vals_list:
            vals["date_created"] = fields.Date.today()

        return super(HelpdeskTicket, self.with_context(context)).create(vals_list)

    def message_post(self, **kwargs):
        # If suppress_mail context is active, skip message_post completely
        if self.env.context.get("suppress_mail"):
            return False  # Do not post message
        return super().message_post(**kwargs)

    def action_mark_cloase(self):
        for rec in self:
            rec.date_resolved = fields.Date.today()

    def calculate_time_taken(self):
        for rec in self:
            if rec.date_resolved and rec.date_created:
                time_taken = rec.date_resolved - rec.date_created
                return time_taken.days
            else:
                return 0

    def action_submit(self):
        pass

    def _creation_subtype(self):
        return None
