# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C):
#        2012-Today Serpent Consulting Services (<http://www.serpentcs.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    "name": "Positional File",
    "version": "8.0.1.1.0",
    "author": "KAZACUBE",
    "contributors": [
        "Abdellatif BENZBIRIA <abenzbiria@kazacube.com>",
    ],
    "category": "Tools",
    "website": "http://www.kazacube.com",
    "license": "GPL-3 or any later version",
    "description": """
    This module provides the functionality to add, update or remove the values
    of more than one records on the fly at the same time.
    You can configure mass editing for any OpenERP model.
    For more details/customization/feedback contact us on
    contact@kazacube.com.
    """,
    'depends': ['base'],
    'data': [
       # "security/ir.model.access.csv",
        'data/etebac3.xml',
        'views/positional_file_view.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
