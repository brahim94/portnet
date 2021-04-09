# -*- coding: utf-8 -*-
from openerp import http

# class PortnetReportExtend(http.Controller):
#     @http.route('/portnet_report_extend/portnet_report_extend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/portnet_report_extend/portnet_report_extend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('portnet_report_extend.listing', {
#             'root': '/portnet_report_extend/portnet_report_extend',
#             'objects': http.request.env['portnet_report_extend.portnet_report_extend'].search([]),
#         })

#     @http.route('/portnet_report_extend/portnet_report_extend/objects/<model("portnet_report_extend.portnet_report_extend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('portnet_report_extend.object', {
#             'object': obj
#         })