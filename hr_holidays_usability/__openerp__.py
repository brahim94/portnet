# -*- coding: utf-8 -*-
##############################################################################
#
#    HR Holidays Usability module for Odoo
#    Copyright (C) 2015 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'HR Holidays Usability',
    'version': '0.1',
    'category': 'Human Resources',
    'license': 'AGPL-3',
    'summary': 'Better usability for the management of holidays',
    'description': '',
    'depends': ['base','hr_holidays','hr_timesheet_sheet'],
    'data': [
	    'views/hr_public_holidays_view.xml',
        'wizard/mass_allocation/hr_holidays_mass_allocation_view.xml',
        'wizard/holidays_post/hr_holidays_post_view.xml',
        'report/hr_holidays_employee_counter_view.xml',
        'views/hr_holidays_view.xml',
        'views/hr_holidays_mail.xml',
        'views/res_company_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_analytic_timesheet.xml',
        'views/hr_holidays_status.xml',
        'security/holiday_security.xml',
        'security/ir.model.access.csv',
        ],
    'installable': True,
    'application': True
}
