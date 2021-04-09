# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp

class sale_order(models.Model):
    _inherit = 'sale.order'


    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        # pricelist
        pricelist = False
        if part.categ_id: pricelist = part.categ_id.pricelist_id.id
        if not part.categ_id and not part.categ_id.pricelist_id and part.property_product_pricelist:
            pricelist = part.property_product_pricelist.id
        # pricelist
        invoice_part = self.pool.get('res.partner').browse(cr, uid, addr['invoice'], context=context)
        payment_term = invoice_part.property_payment_term and invoice_part.property_payment_term.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'user_id': dedicated_salesman,
        }
        delivery_onchange = self.onchange_delivery_id(cr, uid, ids, False, part.id, addr['delivery'], False,  context=context)
        val.update(delivery_onchange['value'])
        if pricelist:
            val['pricelist_id'] = pricelist
        if not self._get_default_section_id(cr, uid, context=context) and part.section_id:
            val['section_id'] = part.section_id.id
        sale_note = self.get_salenote(cr, uid, ids, part.id, context=context)
        if sale_note: val.update({'note': sale_note})
        return {'value': val}


sale_order()