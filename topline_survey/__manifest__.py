# -*- coding: utf-8 -*-
{
    'name': "HR Survey Extension",
    'version': '1.0',
    'summary': """
        -Modification to HR Survey
    """,
    'description': """
        Extension of HR Survey: Add new Survey creator group and modify access rights for users and creators
    """,
    'author': "MCEE Solutions",
    'website': "https://www.mceesolutions.com/",
    'category': 'topline',
    'depends': [
        'survey',
        'hr_appraisal'
    ],
    'data': [
        'security/access_security.xml',
        'security/ir.model.access.csv',
    ],
}
