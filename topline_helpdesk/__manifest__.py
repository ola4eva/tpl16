{
    "name": "Helpdesk Enhancement",
    "version": "1.0",
    "category": "Helpdesk",
    "summary": "Enhancements for the Helpdesk module",
    "description": """
This module provides enhancements for the Helpdesk module in Odoo. It includes features such as:
- Ability to send notifications on button click ticket templates
- Ability to track the time taken to resolve tickets
""",
    "author": "HyperIT Consultants",
    "website": "https://yourwebsite.com",
    "depends": ["helpdesk"],
    "data": [
        "data/email_template.xml",
        "views/helpdesk_ticket_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}