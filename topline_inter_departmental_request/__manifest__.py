# -*- coding: utf-8 -*-
{
    'name': "Inter Departmental Request",

    'summary': """
        Interdepartmental request""",

    'description': """
        Long description of module's purpose
    """,

    'author': "HyperIT Consulting",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/seq_data.xml',
        'data/email_data.xml',
        'views/request_views.xml',
    ],
}