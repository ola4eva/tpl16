# -*- coding: utf-8 -*-
# Part of Odoo, Aktiv Software.
# See LICENSE file for full copyright & licensing details.

# Author: Aktiv Software.
# mail:   odoo@aktivsoftware.com
# Copyright (C) 2015-Present Aktiv Software PVT. LTD.
# Contributions:
#           Aktiv Software:
#               - Parth Radadia
#               - Shahil Chauhan
#               - Harshil Soni

{
    "name": "Merge Purchase Order",
    "category": "Purchases",
    "summary": "This module will merge purchase order.",
    "version": "16.0.1.0.0",
    "website": "http://www.aktivsoftware.com",
    "author": "Aktiv Software",
    "description": "Merge Purchase Order",
    "license": "AGPL-3",
    "depends": ["purchase", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/merge_puchase_order_wizard_view.xml",
    ],
    "images": [
        "static/description/banner.jpg",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
