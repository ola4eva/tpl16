# -*- coding: utf-8 -*-
{
    'name': "Store Request",

    'summary': """
        Topline store request""",

    'description': """
        topline store request
    """,

    'author': "HyperIT Consultants",
    'website': "https://www.yourcompany.com",

    'category': 'Inventory',
    'version': '0.1',

    'depends': ['stock'],

    'data': [
        'data/ir_sequence.xml',
        'data/store_request_data.xml',
        'security/ir.model.access.csv',
        'views/stock_move_views.xml',
        # 'views/views.xml',
    ],
}
