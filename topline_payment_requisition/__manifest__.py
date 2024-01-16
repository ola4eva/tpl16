# -*- coding: utf-8 -*-
{
    'name': "Payment Requisition Enhancement",

    'summary': """
        Enhancement of Payment Requisition""",

    'description': """
        Long description of module's purpose
    """,

    'author': "MCEE Business Solutiions",
    'website': "http://www.mceesolutions.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
        'base',
        'topline',
    ],

    'license': 'LGPL-3',

    'data': [
        'security/access_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/payment_requisition_views.xml',
        'views/res_company_view.xml',
        'wizard/payment_view.xml',
        'wizard/reject_request_views.xml',
    ],
}