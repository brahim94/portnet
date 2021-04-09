# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    is_global_calendar = fields.Boolean(string='Global Holidays Schedule')
    weekend_ids = fields.Many2many('weekday.weekday', 'rel_weekday_resource', 'weekday_id', 'resource_id', string='Weekends')

    def _check_holiday_status(self, actual_days, actual_date):
        resource_id = self.env['resource.calendar'].search([('is_global_calendar', '=', True)])
        if len(resource_id) > 1:
            raise UserError(_("System found more than one Gloabl Leaves configuration."))
        elif len(resource_id) == 1:
            if isinstance(actual_date, str):
                actual_date = fields.Date.from_string(actual_date)
            date = actual_date + timedelta(days=actual_days)
            while (resource_id.global_leave_ids.filtered(lambda a: a.date_from.date() <= date and a.date_to.date() >= date)) or (date.strftime("%A") in resource_id.weekend_ids.mapped('name')):
                actual_days += 1
                date = actual_date + timedelta(days=actual_days)
            return actual_days
        else:
            raise UserError(_("Gloabl Leaves configuration not found in system."))


class WeekdayWeekday(models.Model):
    _name = 'weekday.weekday'
    _description = 'Week Days'

    name = fields.Char(string='Weekends', required=True)
