# -*- coding: utf-8 -*-

from datetime import date
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        payment = self.env['payment.requisition.form'].search(
            [('name', '=', self.ref)])
        if payment:
            payment.write({'state': 'post'})
        return super(AccountMove, self).action_post()


class Picking(models.Model):
    _name = "stock.picking"
    _inherit = 'stock.picking'
    _order = 'create_date DESC'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Line Manager Approved'),
        ('qa_qc_approve', 'QA/QC Approved'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled'),
    ], string='Status',
        # compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")
    picking_type_name = fields.Char(
        string='Picking Type Name', related='picking_type_id.name')
    active = fields.Boolean('Active', default=True)

    # @api.depends('move_type', 'move_lines.state', 'move_lines.picking_id')
    # def _compute_state(self):
    #     ''' State of a picking depends on the state of its related stock.move
    #     - Draft: only used for "planned pickings"
    #     - Waiting: if the picking is not ready to be sent so if
    #       - (a) no quantity could be reserved at all or if
    #       - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
    #     - Waiting another move: if the picking is waiting for another move
    #     - Ready: if the picking is ready to be sent so if:
    #       - (a) all quantities are reserved or if
    #       - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
    #     - Done: if the picking is done.
    #     - Cancelled: if the picking is cancelled
    #     '''
    #     if not self.move_lines:
    #         self.state = 'draft'
    #     elif any(move.state == 'draft' for move in self.move_lines):  # TDE FIXME: should be all ?
    #         self.state = 'draft'
    #     elif all(move.state == 'cancel' for move in self.move_lines):
    #         self.state = 'cancel'
    #     elif all(move.state in ['cancel', 'done'] for move in self.move_lines):
    #         self.state = 'done'
    #     else:
    #         relevant_move_state = self.move_lines._get_relevant_state_among_moves()
    #         if relevant_move_state == 'partially_available':
    #             self.state = 'assigned'
    #         else:
    #             self.state = relevant_move_state

    def unlink(self):
        for picking in self:
            store_request_picking_type = self.env.ref(
                "topline.stock_picking_type_emp")
            if picking.picking_type_id == store_request_picking_type:
                raise UserError(
                    "You are not allowed to delete store requests, you may consider archiving instead!!!")
        return super(Picking, self).unlink()

    def button_submit(self):
        self.write({'state': 'submit'})
        for move in self.move_lines:
            move.state = 'submit'
        partner_ids = []
        if self.employee_id.parent_id.user_id:
            partner_ids.append(
                self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Store request {} for {} needs approval".format(
            self.name, self.employee_id.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False

    def action_confirm(self):
        self.write({'is_locked': True})
        for move in self.move_lines:
            move.state = 'confirmed'
        res = super(Picking, self).action_confirm()
        if self.picking_type_id.name == 'Staff Store Requests':
            self.button_approve_srt()
            group_id = self.env['ir.model.data'].xmlid_to_object(
                'stock.group_stock_manager')
            user_ids = []
            partner_ids = []
            for user in group_id.users:
                user_ids.append(user.id)
                partner_ids.append(user.partner_id.id)
            self.message_subscribe(partner_ids=partner_ids)
            subject = "Store request {} has been authorized".format(self.name)
            self.message_post(subject=subject, body=subject,
                              partner_ids=partner_ids)
            return False
        return res

    def action_line_manager_approval(self):
        self.write({'state': 'approve'})
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_qa')
        for move in self.move_lines:
            move.state = 'approve'
        self.manager_confirm()
        subject = "Store request {} for {} has been approved by line manager".format(
            self.name, self.employee_id.name)
        partner_ids = []
        user_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def action_qa_qc_approval(self):
        self.write({'state': 'qa_qc_approve'})
        for move in self.move_lines:
            move.state = 'qa_qc_approve'
        self.manager_confirm()
        subject = "Store request {} for {} has been approved by QA/QC".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        self.send_store_request_mail()

    def manager_confirm(self):
        for order in self:
            order.write({'man_confirm': True})
        return True

    def _default_owner(self):
        return self.env.context.get('default_employee_id') or self.env['res.users'].browse(self.env.uid).partner_id

    def _default_employee(self):
        self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    owner_id = fields.Many2one('res.partner', 'Owner',
                               states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=_default_owner,
                               help="Default Owner")

    employee_id = fields.Many2one('hr.employee', 'Requesting Employee',
                                  states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, default=_default_employee,
                                  help="Default Owner")

    request_date = fields.Date(string='Date', default=date.today())
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', related='employee_id.department_id')

    total_price = fields.Float(
        string='Total',
        # compute='_total_price',
        readonly=True, store=True)
    man_confirm = fields.Boolean(
        'Manager Confirmation', tracking=True)
    client_id = fields.Many2one(
        'res.partner', string='Client', index=True, ondelete='cascade', required=False)
    need_approval = fields.Boolean(
        'Need Approval', tracking=True, copy=False)
    total_cost = fields.Float(
        string='Total Cost', compute='_total_cost', tracking=True, readonly=True)
    project_id = fields.Many2one(
        'project.project', string='Project', index=True, ondelete='cascade', required=False)
    project_description = fields.Char('Project Description', copy=False)

    rejection_reason = fields.Many2one(
        'stock.rejection.reason', string='Rejection Reason', index=True, tracking=True)

    @api.depends('move_ids_without_package.product_uom_qty')
    def _total_cost(self):
        for a in self:
            for line in a.move_ids_without_package:
                a.total_cost += line.price_cost * line.product_uom_qty

    def button_reset(self):
        self.mapped('move_lines')._action_cancel()
        self.write({'state': 'draft'})
        return {}

    def send_store_request_mail(self):
        if self.picking_type_id.name == "Staff Store Requests" and self.state in ['draft', 'approve', 'waiting', 'confirmed']:
            group_id = self.env['ir.model.data'].xmlid_to_object(
                'stock.group_stock_manager')
            user_ids = []
            partner_ids = []
            for user in group_id.users:
                user_ids.append(user.id)
                partner_ids.append(user.partner_id.id)
            self.message_subscribe(partner_ids=partner_ids)
            subject = "Store request {} for {} needs Validation from Stock".format(
                self.name, self.employee_id.name)
            self.message_post(subject=subject, body=subject,
                              partner_ids=partner_ids)
            return False
        return True

    def send_store_request_done_mail(self):
        if self.state in ['done']:
            subject = "Store request '{}', for {} has been approved and validated".format(
                self.name, self.employee_id.name)
            partner_ids = []
            for partner in self.sheet_id.message_partner_ids:
                partner_ids.append(partner.id)
            self.sheet_id.message_post(
                subject=subject, body=subject, partner_ids=partner_ids)

    def button_reject(self):
        self.write({'state': 'reject'})
        subject = "Store request '{}', for {} has been rejected".format(
            self.name, self.employee_id.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)

    def button_approve_srt(self):
        self.need_approval = False
        return {}

    # @api.depends('move_lines.price_unit')
    # def _total_price(self):
    #     for line in self.move_lines:
    #         self.total_price += line.price_subtotal

    def create_atp_order(self):
        """
        Method to open create atp form
        """
        view_ref = self.env['ir.model.data'].get_object_reference(
            'topline', 'topline_atp_form_view')
        view_id = view_ref[1] if view_ref else False

        for subscription in self:
            order_lines = []
            for line in subscription.move_lines:
                order_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'qty': line.product_uom_qty,
                    'date_planned': date.today(),
                    'size': line.store_request_size,
                    'brand_id': line.brand_id.id,
                    'certificate_required': line.certificate_required,
                    'price': line.product_id.standard_price,
                }))

        res = {
            'type': 'ir.actions.act_window',
            'name': ('ATP FORM'),
            'res_model': 'atp.form',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {'default_project_des': self.project_description, 'default_stock_source': self.name, 'default_expected_date': self.scheduled_date, 'default_atp_form_line_ids': order_lines}
        }
        return res


class StockRejectionReason(models.Model):
    _name = "stock.rejection.reason"
    _description = 'Reason for Rejecting Requests'

    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active', default=True)


class StockPickingRejection(models.TransientModel):
    _name = 'stock.picking.rejected'
    _description = 'Get Rejection Reason'

    rejection_reason_id = fields.Many2one(
        'stock.rejection.reason', 'Rejection Reason')

    def action_rejection_reason_apply(self):
        leads = self.env['stock.picking'].browse(
            self.env.context.get('active_ids'))
        leads.write({'rejection_reason': self.rejection_reason_id.id})
        return leads.button_reject()


class BrandType(models.Model):
    _name = "brand.type"
    _description = 'Make/Brand'

    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active', default=True)


class ExpenseRef(models.Model):
    _name = 'hr.expense'
    _inherit = 'hr.expense'
    _order = 'create_date DESC'

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')
    description = fields.Char(string='Expense Desciption')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hr.expense') or '/'
        return super(ExpenseRef, self).create(vals_list)


class HrExpenseSheet(models.Model):
    _name = "hr.expense.sheet"
    _inherit = 'hr.expense.sheet'
    _order = 'create_date DESC'

    state = fields.Selection([('submit', 'Submitted'),
                              ('line_approval', 'Line Manager Approved'),
                              ('audit', 'Internal Review'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('open', 'Open'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='submit', required=True,
                             help='Expense Report State')

    name = fields.Char(string='Expense Report Summary',
                       readonly=True, required=True)
    description = fields.Char(
        string='Expense Desciption', readonly=True, compute='get_desc')

    def get_desc(self):
        for expense in self.expense_line_ids:
            if expense.description:
                self.description = expense.description
                break

    '''
    
    def button_line_manager_approval(self):
        self.write({'state': 'line_approval'})
        subject = "Expense '{}' has been approved by Line Manager".format(self.name)
        partner_ids = []
        for partner in self.sheet_id.message_partner_ids:
            partner_ids.append(partner.id)
        self.sheet_id.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return {}
    '''

    def button_md_approval(self):
        self.write({'state': 'approve'})
        subject = "Expense '{}' has been approved by MD".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return {}

    def button_audit_approval(self):
        self.write({'state': 'audit'})
        subject = "Expense '{}' has been approved by Audit".format(self.name)
        partner_ids = []
        for partner in self.message_partner_ids:
            partner_ids.append(partner.id)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return {}

    def expense_audit_approval_notification(self):
        group_id = self.env['ir.model.data'].xmlid_to_object(
            'topline.group_internal_audit')
        user_ids = []
        partner_ids = []
        for user in group_id.users:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "Expense '{}' needs approval".format(self.name)
        self.message_post(subject=subject, body=subject,
                          partner_ids=partner_ids)
        return False
    '''
    
    def expense_audit_approval_notification(self):
        subject = "Expense '{}' has been approved".format(self.name)
        partner_ids = []
        for partner in self.sheet_id.message_partner_ids:
            partner_ids.append(partner.id)
        self.sheet_id.message_post(subject=subject,body=subject,partner_ids=partner_ids)
    '''

    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(
                _("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot approve your own expenses"))

            if not self.env.user in current_managers:
                raise UserError(
                    _("You can only approve your department expenses"))

        responsible_id = self.user_id.id or self.env.user.id
        self.write({'state': 'line_approval', 'user_id': responsible_id})
        self.activity_update()
        # self.expense_audit_approval_notification()

    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(
                _("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(
                _("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
            self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        self.filtered(lambda hol: hol.state == 'line_approval').activity_feedback(
            ['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state == 'cancel').activity_unlink(
            ['hr_expense.mail_act_expense_approval'])


class StockMove(models.Model):
    _inherit = "stock.move"

    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('qa_qc_approve', 'QA/QC Approved'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")

    def _valid_field_parameter(self, field, name):
        # EXTENDS models
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    @api.depends('product_uom_qty', 'price_cost')
    def _compute_subtotal(self):
        for line in self:
            self.price_subtotal = self.product_uom_qty * line.price_cost

    def _default_cost(self):
        return self.product_id.standard_price

    price_cost = fields.Float(
        string="Cost", related='product_id.standard_price')
    price_subtotal = fields.Float(
        string="Price Subtotal", compute="_compute_subtotal", readonly=True)

    store_request_size = fields.Char('Size', copy=False)
    brand_id = fields.Many2one('brand.type', 'Make/Brand', copy=False)
    certificate_required = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Certificate Required', readonly=False, index=True, copy=False, tracking=True,)

    def _get_relevant_state_among_moves(self):
        # We sort our moves by importance of state:
        #     ------------- 0
        #     | Assigned  |
        #     -------------
        #     |  Waiting  |
        #     -------------
        #     |  Partial  |
        #     -------------
        #     |  Confirm  |
        #     ------------- len-1
        sort_map = {
            'assigned': 4,
            'waiting': 3,
            'partially_available': 2,
            'confirmed': 1,
        }
        moves_todo = self\
            .filtered(lambda move: move.state not in ['cancel', 'done'])\
            .sorted(key=lambda move: (sort_map.get(move.state, 0)))
        # The picking should be the same for all moves.
        if moves_todo[0].picking_id.move_type == 'one':
            most_important_move = moves_todo[0]
            if most_important_move.state == 'confirmed':
                return 'confirmed' if most_important_move.product_uom_qty else 'assigned'
            elif most_important_move.state == 'partially_available':
                return 'confirmed'
            else:
                return moves_todo[0].state or 'draft'
        elif moves_todo[0].state != 'assigned' and any(move.state in ['assigned', 'partially_available'] for move in moves_todo):
            return 'partially_available'
        else:
            least_important_move = moves_todo[-1]
            if least_important_move.state == 'confirmed' and least_important_move.product_uom_qty == 0:
                return 'assigned'
            else:
                return moves_todo[-1].state or 'draft'


class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = ['stock.move.line', 'mail.thread', 'mail.activity.mixin']
