# -*- coding: utf-8 -*-

from odoo import fields, models, _


class Lead(models.Model):
    _name = "crm.lead"
    _inherit = 'crm.lead'

    bid_category = fields.Selection([('technical', 'Technical Bid'), (
        'commercial', 'Commercial Bid')], string='Bid Category', required=False)

    contract_start_date = fields.Date(string='Start Date')
    contract_end_date = fields.Date(string='End Date')
    document_submission_date = fields.Date(string='Document Submission Date')

    
    def write(self, vals):
        if vals.get('stage_id.name', 'Negotiation') == 'Negotiation':
            group_id = self.env['ir.model.data'].xmlid_to_object(
                'account.group_account_manager')
            user_ids = []
            partner_ids = []
            for user in group_id.users:
                user_ids.append(user.id)
                partner_ids.append(user.partner_id.id)
            self.message_subscribe(partner_ids=partner_ids)
            subject = "Budget report is needed for this oppurtunity '{}' ".format(
                self.name)
            self.message_post(subject=subject, body=subject,
                              partner_ids=partner_ids)
        return super(Lead, self).write(vals)


