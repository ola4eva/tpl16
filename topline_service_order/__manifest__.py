# -*- coding: utf-8 -*-
{
    'name': "Service Order",

    'summary': """
        Service Order""",

    'description': """
        Service Order
    """,

    'author': "Hyper IT Consultatns",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1.0',

    'license': 'LGPL-3',

    'depends': [
        'topline',
    ],

    'data': [
        'data/ir_sequence.xml',
        'data/service_order_data.xml',
        'security/ir.model.access.csv',
        'views/service_order_views.xml',

    ],
}
