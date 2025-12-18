# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "User Audit | User Activity Audit",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Follow Users Traces,Audit Trail,User Log,Log Report, Record Log,Record Information,User Activity log, Record History,Log History,User Activity Audit Log,Manage Audit Logs,Track every Users Operation,Delete Log,audit user activity Odoo",
    "description": """This module allows to track all user's operations performed on data models such as create, read, write and delete. You can track every user's activity on all the objects of the system. You can group by audit logs with different dimensions like user, object & type. The log view contains details about each operation like date, record id, record object name, user name, type, old and new values of each modified field, etc.""",
    "version": "16.0.3",
    'depends': ['base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'security/sh_user_audit_groups.xml',
        'data/sh_user_audit_data.xml',
        'views/sh_user_audit_views.xml',
        'wizard/sh_clear_log_views.xml',
        'views/sh_user_audit_logs_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    "images": ["static/description/background.png", ],
    "price": 40,
    "currency": "EUR"
}
