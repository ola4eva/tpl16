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
    # 'version': '16.0.0.1',

    'depends': [
        'purchase',
        'topline',
        'hr',
        'topline_service_order',
        'topline_atp',
    ],
    'license': 'LGPL-3',
    'data': [
        'security/follower_groups.xml',
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml'
    ]
}