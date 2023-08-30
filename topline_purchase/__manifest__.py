# -*- coding: utf-8 -*-
{
    'name': "Topline Purchase",

    'summary': """
        Modifications to Purchase Order""",

    'description': """
        Modifications to Purchase Order
    """,

    'author': "HyperIT Consulting",
    'website': "http://www.yourcompany.com",

    'category': 'Purchase',
    'version': '0.1',

    'depends': [
        'purchase',
        'topline',
        'hr',
    ],

    'data': [
        'views/purchase_order_views.xml'
    ]
}