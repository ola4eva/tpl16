# -*- coding: utf-8 -*-
{
    'name': "Topline Limited Reminder",

    'summary': """
        Topline Modules""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MCEE Solutions",
    'website': "http://www.mceesolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'topline',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'mail', 
        'purchase',
        'topline',
    ],
    # always loaded
    'data': [
        #'security/topline_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'license': 'LGPL-3',
    'qweb': [
        #'views/chatter.xml'
    ],
}
