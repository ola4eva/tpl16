# -*- coding: utf-8 -*-
##############################################################################
#
#    Ballotnet Solutions Ltd.
#    Copyright (C) 2018-TODAY Ballotnet Solutions Ltd (komolafetosin@gmail.com).
#    Author: Tosin Komolafe(<komolafetosin@gmail.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Topline HR Directory',
    'summary': """Extra functionalities on Employee Directory""",
    'version': '12.0.1.0.1',
    'description': """Sunray HR""",
    'author': 'MCEE',
    'company': 'MCEE Solutions Ltd',
    'category': 'Extra Tools',
    'license': 'AGPL-3',
    'website': 'http://mceesolutions.com',
    'depends': ['hr_payroll'],
    'sequence': '1000',
    'data': [
        'views/hr_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}


