# -*- coding: utf-8 -*-
# from odoo import http


# class TechReportsExtention(http.Controller):
#     @http.route('/tech_reports_extention/tech_reports_extention/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tech_reports_extention/tech_reports_extention/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tech_reports_extention.listing', {
#             'root': '/tech_reports_extention/tech_reports_extention',
#             'objects': http.request.env['tech_reports_extention.tech_reports_extention'].search([]),
#         })

#     @http.route('/tech_reports_extention/tech_reports_extention/objects/<model("tech_reports_extention.tech_reports_extention"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tech_reports_extention.object', {
#             'object': obj
#         })
