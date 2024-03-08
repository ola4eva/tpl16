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

    'depends': ['topline_payment_requisition'],

    'data': [
        'security/ir.model.access.csv',
        'views/service_order_views.xml',
    ],
}
