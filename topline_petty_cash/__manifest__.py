# -*- coding: utf-8 -*-
{
    'name': "Petty Cash",

    'summary': """
        Petty cash module""",

    'description': """
        Petty cash module
    """,

    'author': "Olalekan Babawale",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'license': 'LGPL-3',
    'version': '0.1',
    'depends': ['hr_expense'],

    'data': [
        'security/ir.model.access.csv',
        'views/petty_cash_views.xml',
    ],
}
