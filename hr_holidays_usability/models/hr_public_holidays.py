#-*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 One Click Software (http://oneclick.solutions)
#    and Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from datetime import date
from openerp import fields, models, api, _

class HrHolidays(models.Model):
    
    _name = 'hr.holidays.public'
    _description = 'Public Holidays'
    _order = 'year'
    
    _sql_constraints = [
        ('year_unique', 'UNIQUE(year)', _('Duplicate year!')),
    ]
    
    year = fields.Char(string='calendar Year', required=True)
    line_ids = fields.One2many('hr.holidays.public.line', 'holidays_id', string='Holiday Dates')

    @api.multi
    def is_public_holiday(self, dt):
        ph_obj = self.env['hr.holidays.public']
        ph_ids = ph_obj.search([('year', '=', dt.year)])
        if len(ph_ids) == 0:
            return False
        for line in ph_obj.browse(ph_ids[0].id).line_ids:
            if date.strftime(dt, "%Y-%m-%d") == line.date:
                return True
        return False
    
    @api.multi
    def get_holidays_list(self, year):
        res = []
        ph_ids = self.search([('year', '=', year)])
        if len(ph_ids) == 0:
            return res
        [res.append(l.date) for l in self.browse(ph_ids[0]).line_ids]
        return res


class HrHolidaysLine(models.Model):
    
    _name = 'hr.holidays.public.line'
    _description = 'Public Holidays Lines'
    _order = "date, name desc"


    name = fields.Char(string='Name', required=True)
    date = fields.Date(string='Date', required=True)
    holidays_id = fields.Many2one('hr.holidays.public', string = 'Holiday Calendar Year')
    variable = fields.Boolean('Date may change')
