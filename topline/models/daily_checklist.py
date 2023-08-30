# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from datetime import date


class DailyChecklist(models.Model):
    _name = 'daily.checklist'
    _description = 'Daily Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    '''
    livestream = fields.Char(string='LIVESTREAM DISPLAY MONITOR', required=True, track_visibility='onchange')
    #livestream_bool = fields.Boolean(string='LIVESTREAM DISPLAY MONITOR', required=True, track_visibility='onchange')
    accounts_server = fields.Char(string='ACCOUNTS SERVER', required=True, track_visibility='onchange')
    #accounts_server_bool = fields.Boolean(string='ACCOUNTS SERVER', required=True, track_visibility='onchange')
    backup_system = fields.Char(string='BACK-UP SYSTEM', required=True, track_visibility='onchange')
    #backup_system_bool = fields.Boolean(string='BACK-UP SYSTEM', required=True, track_visibility='onchange')
    mtn_radio = fields.Char(string='MTN RADIO', required=True, track_visibility='onchange')
    #mtn_radio_bool = fields.Boolean(string='MTN RADIO', required=True, track_visibility='onchange')
    mtn_rounter_wan = fields.Char(string='MAIN ROUTER (WAN)', required=True, track_visibility='onchange')
    #mtn_rounter_wan_bool = fields.Boolean(string='MAIN ROUTER (WAN)', required=True, track_visibility='onchange')
    wireless_bridge_a = fields.Char(string='WIRELESS BRIDGE A', required=True, track_visibility='onchange')
    #wireless_bridge_a_bool = fields.Boolean(string='WIRELESS BRIDGE A', required=True, track_visibility='onchange')
    wireless_bridge_b = fields.Char(string='WIRELESS BRIDGE B', required=True, track_visibility='onchange')
    #wireless_bridge_b_bool = fields.Boolean(string='WIRELESS BRIDGE B', required=True, track_visibility='onchange')
    intercom = fields.Char(string='INTERCOM', required=True, track_visibility='onchange')
    #intercom_bool = fields.Boolean(string='INTERCOM', required=True, track_visibility='onchange')
    '''

    state = fields.Selection([
        ('new', 'New'),
        ('on', 'Powered On'),
        ('of', 'Powered Off'),
    ], string='Status', readonly=False, index=True, copy=False, default='new', track_visibility='onchange')

    date = fields.Date(string='Date', required=True, default=date.today())

    daily_checklist_power_on_line_ids = fields.One2many(
        'daily.checklist.power.on.line', 'daily_checklist_id', string="Daily Checklist Power On Lines", copy=True)
    daily_checklist_power_off_line_ids = fields.One2many(
        'daily.checklist.power.off.line', 'daily_checklist_id', string="Daily Checklist Power Off Lines", copy=True)

    name = fields.Char('Order Reference', readonly=True,
                       required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'daily.checklist') or '/'
        return super(DailyChecklist, self).create(vals)

    def prepare_on_lines(self):
        self.ensure_one()
        sub = self.env['daily.checklist.equipment'].search(
            [('active', '=', True)])
        for check in sub:
            # for line in self.daily_checklist_power_on_line_ids:
            self.daily_checklist_power_on_line_ids.create({
                'daily_checklist_id': self.id,
                'equipment_id': check.id,
                'equipment_on_bool': True,
                'time': datetime.datetime.now().time()
            })
        self.write({'state': 'on'})

    def prepare_off_lines(self):
        self.ensure_one()
        sub = self.env['daily.checklist.equipment'].search(
            [('active', '=', True)])
        for check in sub:
            # for line in self.daily_checklist_power_on_line_ids:
            self.daily_checklist_power_off_line_ids.create({
                'daily_checklist_id': self.id,
                'equipment_id': check.id,
                'equipment_off_bool': True,
                'time': datetime.datetime.now().time()
            })
        self.write({'state': 'of'})


class DailyChecklistPowerOnLines(models.Model):
    _name = 'daily.checklist.power.on.line'
    _description = 'Daily Checklist Power On Lines'

    daily_checklist_id = fields.Many2one(
        comodel_name='daily.checklist', string='Daily Checklist')

    equipment_id = fields.Many2one(
        comodel_name='daily.checklist.equipment', string='Daily Checklist Equipment', required=True)
    equipment_on_bool = fields.Boolean(
        string='On', required=True, track_visibility='onchange')
    equipment_off_bool = fields.Boolean(
        string='Off', required=True, track_visibility='onchange')
    time = fields.Char(string='Time')
    remark = fields.Char(string='Remark', required=False,
                         track_visibility='onchange')


class DailyChecklistPowerOffLines(models.Model):
    _name = 'daily.checklist.power.off.line'
    _description = 'Daily Checklist Power Off Lines'

    daily_checklist_id = fields.Many2one(
        comodel_name='daily.checklist', string='Daily Checklist')

    equipment_id = fields.Many2one(
        comodel_name='daily.checklist.equipment', string='Daily Checklist Equipment', required=True)
    equipment_on_bool = fields.Boolean(
        string='On', required=True, track_visibility='onchange')
    equipment_off_bool = fields.Boolean(
        string='Off', required=True, track_visibility='onchange')
    time = fields.Char(string='Time')
    remark = fields.Char(string='Remark', required=False,
                         track_visibility='onchange')


class DailyChecklistEquipment(models.Model):
    _name = 'daily.checklist.equipment'
    _description = 'Daily Checklist Equipments'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(
        string='Active', default=True, required=False, track_visibility='onchange')
