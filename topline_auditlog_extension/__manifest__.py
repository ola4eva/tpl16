# -*- coding: utf-8 -*-
{
    'name': "Topline Audit Log Extension",

    'summary': """
        Topline Audit Log""",

    'description': """
        - Extension of the audit log module for Topline
    """,

    'author': "MCEE Solutions",
    'website': "https://www.mceesolutions.com/",

    'category': 'Tools',
    'version': '0.1',

    'depends': [
        'auditlog',
        'topline',
    ],

    'data': [
        'views/auditlog_extended_view.xml',
    ],

    'demo': [
    ],
}