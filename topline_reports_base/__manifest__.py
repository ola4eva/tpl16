# -*- coding: utf-8 -*-
{
    'name': "Topline Reports Base",

    'summary': """
        Topline Inventory Report Base""",

    'description': """
        - Base for goods received note and product voucher
    """,

    'author': "MCEE Solutions",
    'website': "https://www.mceesolutions.com/",

    'category': 'Stock',
    'version': '0.1',

    'depends': [
        'base', 
        'stock', 
        'web',
        'topline',
    ],
    'license': 'LGPL-3',
    'data': [
        'views/stock_view.xml',
    ],

    'demo': [
    ],
}