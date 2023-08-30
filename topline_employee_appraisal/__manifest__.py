# -*- coding: utf-8 -*-
{
    'name': "Employee Appraisal",

    'summary': """
        Objectives & Key Results for employees""",

    'description': """
        Objectives & Key Results for employees
    """,

    'license': "LGPL-3",

    'author': "HyperIT Consultant",
    'website': "http://ola4eva.github.io",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
        'hr',
    ],

    'data': [
        'security/employee_appraisal_security.xml',
        'security/ir.model.access.csv',
        'data/email_data.xml',
        'data/employee_appraisal_sequence.xml',
        'views/employee_appraisal_views.xml',
        'views/employee_appraisal_template_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
}
