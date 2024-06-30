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

    'license': 'LGPL-3',

    'depends': [
        'stock',
        'hr',
        'project',
        'topline',
    ],

    'data': [
        'data/ir_sequence.xml',
        'data/store_request_data.xml',
        'security/ir.model.access.csv',
        'views/stock_move_views.xml',
        'views/stock_picking_rejection_views.xml',
        'views/stock_picking_views.xml',
    ],
}
