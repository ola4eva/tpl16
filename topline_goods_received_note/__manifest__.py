# -*- coding: utf-8 -*-
{
    'name': "Topline Goods Received Note",

    'summary': """
        Topline Goods Recevied Note""",

    'description': """
        - Goods Received Note
    """,

    'author': "MCEE Solutions",
    'website': "https://www.mceesolutions.com/",

    'category': 'Stock',
    'license': 'LGPL-3',
    'version': '0.1',
    'depends': [
        'base', 
        'stock', 
        'web', 
        'topline_reports_base',
    ],

    'data': [
        'report/goods_received_note.xml',
    ],

    'demo': [
    ],
}