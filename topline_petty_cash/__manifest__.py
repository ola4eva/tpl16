# -*- coding: utf-8 -*-
{
    'name': "Petty Cash",

    'summary': """
        Petty cash module""",

    'description': """
        Petty cash module
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['hr_expense'],

    'data': [
        'security/ir.model.access.csv',
        'views/petty_cash_views.xml',
    ],
}