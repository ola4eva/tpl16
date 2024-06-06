# -*- coding: utf-8 -*-
{
    'name': "Authority To Purchase",

    'summary': """
        Authority to purchase""",

    'description': """
        Authority to purchase
    """,

    'author': "HyperIT Consultants",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'license': 'LGPL-3',

    'depends': [
        'topline_payment_requisition',
        'topline_purchase',
    ],

    # always loaded
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/atp_views.xml',

    ],
}
