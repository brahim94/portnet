# -*- coding: utf-8 -*-
from openerp import http

# class HrHolidaysUsabilityExtra(http.Controller):
#     @http.route('/hr_holidays_usability_extra/hr_holidays_usability_extra/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_holidays_usability_extra/hr_holidays_usability_extra/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_holidays_usability_extra.listing', {
#             'root': '/hr_holidays_usability_extra/hr_holidays_usability_extra',
#             'objects': http.request.env['hr_holidays_usability_extra.hr_holidays_usability_extra'].search([]),
#         })

#     @http.route('/hr_holidays_usability_extra/hr_holidays_usability_extra/objects/<model("hr_holidays_usability_extra.hr_holidays_usability_extra"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_holidays_usability_extra.object', {
#             'object': obj
#         })