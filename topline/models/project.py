# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Project(models.Model):
    _name = "project.project"
    _inherit = ['project.project', 'mail.thread',
                'mail.activity.mixin', 'rating.mixin']
    _description = "Project"

    _sql_constraints = [
        ('project_code_uniq', 'UNIQUE(project_code)', 'Project Code must be Unique')]

    crm_lead_id = fields.Many2one(comodel_name='crm.lead', string='Lead')

    project_code = fields.Char('Project Code', readonly=True,
                               required=True, index=True, copy=False, default='New')

    site_eng_id = fields.Many2one(
        comodel_name="hr.employee", string="Site Engineer", required=False, )
    project_team_ids = fields.Many2many(
        comodel_name="hr.employee", string="Project Team", )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('project_code', 'New') == 'New':
                vals['project_code'] = self.env['ir.sequence'].next_by_code(
                    'project.code') or '/'
        return super(Project, self).create(vals_list)
