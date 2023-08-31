# -*- coding: utf-8 -*-
{
    'name': "Topline Limited",

    'summary': """
        Topline Modules""",

    'description': """
        Base for Topline's Odoo implementation.
    """,

    'author': "MCEE Solutions",
    'website': "https://www.mceesolutions.com/",

    'category': 'topline',
    'version': '0.1.1',
    'depends': [
        'base',
        'hr',
        'project',
        'purchase',
        'product',
        'quality_control',
        'maintenance', 
        'crm', 
        'hr_appraisal', 
        'fleet',
        'sale_management',
        'hr_holidays',
        'hr_expense',
        'account_asset',
        'hr_timesheet',
        'helpdesk',
        'hr_recruitment',
    ],
    'data': [
        'security/topline_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/payment_requisition_register_payment.xml',
        'data/mail_template_data.xml',
        'views/hr_expense_views.xml',
        'views/stock_views.xml',
        'views/salary_advance_views.xml',
        'views/crm_lead_views.xml',
        # 'views/report_invoice.xml',
        # 'views/templates.xml',
        # 'views/views.xml',
        # 'views/payment_requisition_form_views.xml',
        # 'views/fleet_vehicle_cost_views.xml',
    ],
}
