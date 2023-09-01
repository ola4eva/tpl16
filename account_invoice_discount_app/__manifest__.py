{
    'name': 'Discounts On Invoices And Bills',
    "author": "Edge Technologies",
    'version': '16.0.1.0',
    'live_test_url': "https://youtu.be/JFkfQ-_-8eQ",
    "images":['static/description/main_screenshot.png'],
    'summary': 'Vendor Bill Discount customer invoice discount on invoice apply discount on invoice & bill Discount apply vendor bill discount order discount supplier invoice discounts on invoice applying discounts on invoice bill discount apply vendor bills discounts',
    'description': "Discounts On Invoices And Bills App Has Contained Invoice Line Discount As well As Invoice Discount in Percentage Or Fixed",
    "license" : "OPL-1",
    'depends': [
        'account',
       
    ],
    'data': [
            'views/res_config_settings_inherited_view.xml',
            'views/account_move_inherited_view.xml',
            # 'report/invoice_report_inherited.xml',


    ],
    'demo': [ ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 10,
    'currency': "EUR",
    'category': 'Accounting',

}
