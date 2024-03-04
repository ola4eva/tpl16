# -*- coding: utf-8 -*-
{
    'name': "Account Invoice Modification",

    'summary': """
        remove background color from total line on invoice""",

    'description': """
        remove background color from total line on invoice
    """,

    'author': "HyperIT Consultants",
    'website': "http://www.mceesolutions.com",

    'category': 'Accounting/Accounting',
    'version': '12.0.1',

    'depends': [
        'account',
    ],

    'license': 'LGPL-3',

    'data': [
        'views/invoice_template.xml'
    ]
}
