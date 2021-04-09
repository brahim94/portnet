# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    def make_purchase_order(self):
    	res = super(PurchaseRequestLineMakePurchaseOrder, self).make_purchase_order()
    	purchase_request = self.env['purchase.request'].browse(self._context.get('active_id'))
    	purchase_request.write({"state": "done"})
    	return res