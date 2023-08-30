# -*- coding: utf-8 -*-
{
    'name': "Topline Vouchers",

    'summary': """
        Topline Voucher and product allocation report""",

    'description': """
        - Stock Issue Voucher
        - Goods Received Note
    """,

    'author': "MCEE Solutions",
    'website': "https://www.mceesolutions.com/",

    'category': 'Stock',
    'version': '0.1',

    'depends': [
        'base', 
        'stock', 
        'web',
        'topline_reports_base',
    ],

    'data': [
        'report/stock_issue_voucher.xml',
    ],

    'demo': [
    ],
}