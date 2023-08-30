from odoo import models, fields

class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ['sale.order']
    _description = "Quotation"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('gm', 'GM Approval'),
        ('md', 'MD Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    
    def button_submit(self):
        self.write({'state': 'gm'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_gm')
        user_ids = []
        partner_ids = []
        # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
        for user in group_id.users:
            user_ids.append(user.id)
            # partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Service Order '{}' needs approval from GM".format(self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    
    def button_submit_to_md(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_md')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Quotation '{}' needs approval from MD".format(self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    
    def action_gm_approval(self):
        self.write({'state': 'md'})
        subject = "Quotation {} has been approved by GM".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.button_submit_to_md()

