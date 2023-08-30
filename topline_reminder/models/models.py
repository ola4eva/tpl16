# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta

class ToplineReminder(models.Model):
    _name = "topline.reminder"
    _description = 'REMINDER'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    def _default_employee(self): # this method is to search the hr.employee and return the user id of the person clicking the form atm
        self.env['res.users'].search([('id','=',self.env.uid)])
        return self.env['res.users'].search([('id','=',self.env.uid)])
    
    name = fields.Char(string='Name', required=True)
    date = fields.Date(string='Reminder Date', required=True)
    date_deadline = fields.Datetime(string='Deadline')
    
    employee_id = fields.Many2one(comodel_name='res.users', string='Owner', default=_default_employee)
    reminder_group_ids = fields.Many2many(comodel_name='res.users', string='Remind', help="Group of persons to be reminded", default=_default_employee)
    
    periodicity = fields.Selection([
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly'),
        ('year', 'Yearly'),
        ], string='Periodicity', readonly=False, index=True, copy=False, default='day', track_visibility='onchange', required=True)
    
    day = fields.Integer(string='Day(s) Before')
    week = fields.Integer(string='Week(s) Before')
    month = fields.Integer(string='Month(s) Before')
    year = fields.Integer(string='Year(s) Before')
    
    file = fields.Binary(string='Document', required=False, store=True)
    datas_fname = fields.Char('File Name')
    
    active = fields.Boolean(string='Active', default=True)
    
    comments = fields.Char(string='Comments')
    
    
    def send_reminder_notification(self):
        reminders = self.env['topline.reminder'].search([])
        
        current_dates = False
        
        for self in reminders:
            if self.date:
                
                current_dates = datetime.datetime.strptime(str(self.date), "%Y-%m-%d")
                if self.periodicity == 'day':
                    current_datesz = current_dates - relativedelta(days=self.day)
                elif self.periodicity == 'week':
                    current_datesz = current_dates - relativedelta(weeks=self.week)
                elif self.periodicity == 'month':
                    current_datesz = current_dates - relativedelta(months=self.month)
                elif self.periodicity == 'year':
                    current_datesz = current_dates - relativedelta(years=self.year)
                
                date_start_day = current_datesz.day
                date_start_month = current_datesz.month
                date_start_year = current_datesz.year
                
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                
                test_today = datetime.datetime.today().strptime(today, "%Y-%m-%d")
                date_start_day_today = test_today.day
                date_start_month_today = test_today.month
                date_start_year_today = test_today.year
                
                
                if date_start_month == date_start_month_today:
                    if date_start_day == date_start_day_today:
                        if date_start_year == date_start_year_today:
                            self.send_the_reminder_notification()
        return
    
    
    def send_the_reminder_notification(self):
        group_id = self.reminder_group_ids
        user_ids = []
        partner_ids = []
        for user in group_id:
            user_ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)
        subject = "This is a reminder for '{}', {}".format(self.name, self.comments)
        body = self.comments
        self.message_post(subject=subject,body=subject,partner_ids=partner_ids)
        return False
        return {}
    
    