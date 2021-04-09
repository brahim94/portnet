# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import time
from dateutil import parser, rrule, relativedelta

import datetime


class stock_invoice_onshipping(models.TransientModel):
    _name = 'stock.invoice.onshipping'
    _inherit = 'stock.invoice.onshipping'

    def default_get(self, cr, uid, fields, context=None):
        res = super(stock_invoice_onshipping, self).default_get(cr, uid, fields, context)
        today = datetime.datetime.now().date()
        res['invoice_date']= today.isoformat()
        return res


    def create_invoice(self, cr, uid, ids, context=None):
        context = dict(context or {})
        picking_pool = self.pool.get('stock.picking')
        data = self.browse(cr, uid, ids[0], context=context)
        journal2type = {'sale':'out_invoice', 'purchase':'in_invoice', 'sale_refund':'out_refund', 'purchase_refund':'in_refund'}
        context['date_inv'] = data.invoice_date
        acc_journal = self.pool.get("account.journal")
        inv_type = journal2type.get(data.journal_type) or 'out_invoice'
        context['inv_type'] = inv_type

        active_ids = context.get('active_ids', [])
        res = picking_pool.action_invoice_create(cr, uid, active_ids,
              journal_id = data.journal_id.id,
              group = data.group,
              type = inv_type,
              context=context)

        # Calcul pénalités
        print "res ==========",res
        penalty_fees_product = self.pool.get('product.product').search(cr , uid, [('supplier_penalty_fees','=',True)])
        if not penalty_fees_product:
            raise exceptions.ValidationError("Veuillez configurer un produit pour les pénalités de retard")
        penalty_fees_product = self.pool.get('product.product').browse(cr, uid, penalty_fees_product[0])
        if penalty_fees_product.penalty_rate <= 0:
            raise exceptions.ValidationError("Le taux pour le calcul des pénalités doit être supérieur à 0")
        for inv_id in res:
            days_count = 0
            days_break = 0
            inv = self.pool.get('account.invoice').browse(cr, uid, inv_id)
            penalty_amount = 0
            for l in inv.invoice_line:
                if l.move_id:
                    delay = 0
                    delay = inv._calculate_diff_days(l.move_id.date_expected, l.move_id.picking_id.date_done or inv.date_invoice)
                    print "delay =", delay
                    breaks = 0
                    for brk in l.move_id.picking_id.project_break_ids:
                        breaks += inv._calculate_diff_days(brk.date_start, brk.date_end)+1
                        print "breaks =", breaks
                    penalty_days = delay - breaks
                    print "penalty_days =",penalty_days
                    penalty_amount += ((l.price_subtotal * penalty_fees_product.penalty_rate))*penalty_days
            # invoice line creation
            print "penalty_amount =",penalty_amount
            if penalty_amount > 0:
                account_id = penalty_fees_product.property_account_expense.id
                if not account_id:
                    raise exceptions.ValidationError("Merci de définir un compte comptable pour le produit de pénalités ( "+penalty_fees_product.name+" )")
                #taxes
                account = penalty_fees_product.property_account_expense
                taxes = penalty_fees_product.taxes_id or account.tax_ids
                fpos = self.pool.get('account.fiscal.position').browse(cr, uid, False)
                fp_taxes = fpos.map_tax(taxes)
                #taxes
                line_vals = {
                    'name': penalty_fees_product.name,
                    'account_id': account_id,
                    'product_id': penalty_fees_product.id,
                    'quantity': 1,
                    'price_unit': penalty_amount > 0 and (penalty_amount)*-1 or 0.00,
                    'uos_id': penalty_fees_product.uom_id.id,
                    'account_analytic_id': False,
                    'invoice_id': inv_id,
                    'invoice_line_tax_id':[(6, 0, fp_taxes.ids)],
                            }
                inv.env["account.invoice.line"].create(line_vals)
                inv.check_total -= penalty_amount
        return res
        # Calcul pénalités

stock_invoice_onshipping()