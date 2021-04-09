# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Piece_Provide_Details(models.Model):
    _name = 'piece.provide.details'
    _rec_name = 'pieces'

    pieces = fields.Text(string='Pièces')
    obligatoire = fields.Boolean(string="Obligatoire",default=False)
    obligatoire_copy = fields.Char(string="Fournie?",copy=False)
    obligatoire_copy1 = fields.Boolean(string="Fournie?",default=False,copy=False)
#     requisition_id = fields.Many2one('purchase.requisition',string="Requisition")
    bidder_id = fields.Many2one('bidder.offers','Bidder')

    @api.model
    def create(self, vals):
        yes_no_flag = 'Non'
        if 'obligatoire' in vals:
            if vals['obligatoire']== True:
                yes_no_flag = 'Oui'
        vals['obligatoire_copy'] = yes_no_flag
        return super(Piece_Provide_Details, self).create(vals)
    
    def write(self, vals):
        yes_no_flag = 'Non'
        if 'obligatoire' in vals:
            if vals['obligatoire']== True:
                yes_no_flag = 'Oui'
        vals['obligatoire_copy'] = yes_no_flag
        res = super(Piece_Provide_Details, self).write(vals)
        return res

class Piece_Provide_Details_Copy(models.Model):
    _name = 'piece.provide.details.copy'
    _rec_name = 'pieces'

    pieces = fields.Text(string='Pièces')
    obligatoire = fields.Boolean(string="Obligatoire",default=False)
    obligatoire_copy = fields.Char(string="Fournie?",copy=False)
    obligatoire_copy1 = fields.Boolean(string="Fournie?",default=False,copy=False)
#     requisition_id = fields.Many2one('purchase.requisition',string="Requisition")
    bidder_copy_id = fields.Many2one('bidder.offers','Bidder')

    @api.model
    def create(self, vals):
        yes_no_flag = 'Non'
        if 'obligatoire' in vals:
            if vals['obligatoire']== True:
                yes_no_flag = 'Oui'
            vals['obligatoire_copy'] = yes_no_flag
        return super(Piece_Provide_Details_Copy, self).create(vals)
    
    def write(self, vals):
        yes_no_flag = 'Non'
        if 'obligatoire' in vals:
            if vals['obligatoire']== True:
                yes_no_flag = 'Oui'
            vals['obligatoire_copy'] = yes_no_flag
        res = super(Piece_Provide_Details_Copy, self).write(vals)
        return res
    


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    piece_provide_ids = fields.Many2many('piece.provide.details',
                                         'rel_purchase_req_piece_provide_tbl',
                                         'requisition_id',
                                         'piece_provide_id',
                                         string="pièces à fournir",copy=False)

#     piece_provide_ids = fields.One2many('piece.provide.details','requisition_id',
#                                         string="pièces à fournir",copy=False)


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    qty_ordered = fields.Float(compute='_compute_ordered_qty', string='Quantité demandée')


class TenderWithdrawals(models.Model):
    _inherit = 'tender.withdrawals'
    visit_date = fields.Boolean(string="Visite effectuée?")


class Partner(models.Model):
    _inherit = "res.partner"

    rc_ex = fields.Char("RC")
    ville_rc_ex = fields.Text("Ville RC")
    ice_ex = fields.Char("ICE")

    @api.depends('is_company')
    def _compute_company_type(self):
        "default always company"
        for partner in self:
            partner.company_type = 'company'


class LotDetails(models.Model):
    _inherit = 'lot.details'
    
    estimated_price = fields.Float(string="Estimated Price")
    caution = fields.Float(string="Caution")
    retenu = fields.Float(string="Holdback")

    @api.depends('product_ids')
    def _set_estimated_price(self):
        for lot_detail in self:
            est_price = 0
#             if lot_detail.requisition_id and lot_detail.requisition_id.line_ids:
#                 for prod_rec in lot_detail.product_ids:
#                     req_lines = lot_detail.requisition_id.line_ids.filtered(lambda x:x.product_id.id == prod_rec.id)
#                     est_price += sum([line.product_qty * line.price_unit for line in req_lines])
            lot_detail.estimated_price = est_price 
            lot_detail.caution = (est_price * 2/100)
            lot_detail.retenu = (est_price * 7/100)

#     @api.model
#     def default_get(self, fields_list):
#         res = super(LotDetails, self).default_get(fields_list)
#         return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
 
    estimated_prc = fields.Float(string="Prix Estime",compute='_set_estimated_po_price')
    ecart= fields.Float(string="Ecart(%)",compute='_set_estimated_po_price')

    def update_sequence(self):
        sequence = 0
        for line in self.order_line:
            sequence += 1
            line.sequence = sequence
        return True

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        if vals.get('order_line'):
            res.update_sequence()
        return res

    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        if vals.get('order_line'):
            self.update_sequence()
        return res

    def _set_estimated_po_price(self):
        for po_rec in self:
            price_est = perc = 0.0
            price_est = sum([line.product_qty * line.estimated_prc for line in po_rec.order_line])
            if price_est > 0.0:
                perc = ((po_rec.amount_total - price_est)* 100) / price_est
            po_rec.estimated_prc = price_est
            po_rec.ecart = perc

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(PurchaseOrder, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                             orderby=orderby, lazy=lazy)
        """
        To show min. value in listview when do group by.
        """
        po_obj = self.env['purchase.order']
        for line in res:
            if '__domain' in line:
                po_obj = self.search(line['__domain'])
            if 'amount_total' in fields:
                if po_obj.mapped('amount_total'):
                    line['amount_total'] = min(po_obj.mapped('amount_total'))
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    estimated_prc = fields.Float(string="Prix Estime",compute='_set_estimated_po_price')
    ecart= fields.Float(string="Ecart(%)",compute='_set_estimated_po_price')


    def _set_estimated_po_price(self):
        for po_rec_line in self:
            perc = 0
            estimated_prc = 0
            if po_rec_line.order_id and po_rec_line.order_id.requisition_id:
                requistion_lines = po_rec_line.order_id.requisition_id.line_ids
                if requistion_lines:
                    req_lines = requistion_lines.filtered(lambda x:x.product_id.id == po_rec_line.product_id.id)
                    if req_lines:
                        estimated_prc = req_lines[0].price_unit
                        if estimated_prc > 0:
                            perc = ((po_rec_line.price_unit - estimated_prc) * 100) / estimated_prc
            po_rec_line.estimated_prc = estimated_prc
            po_rec_line.ecart = perc
