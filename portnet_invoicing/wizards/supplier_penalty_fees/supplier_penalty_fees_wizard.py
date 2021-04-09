# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from dateutil import parser, rrule, relativedelta
from datetime import date, timedelta

class supplier_penalty_fees_wizard(models.TransientModel):
    _name = 'supplier.penalty.fees.wizard'

    invoice_id = fields.Many2one(comodel_name="account.invoice", string="Facture", required=False)
    penalty_fees_product_id = fields.Many2one(comodel_name="product.product", string="Pénalités à appliquer", required=False, domain=[('supplier_penalty_fees','=',True)])
    base_amount = fields.Float(string="Montant facture", digits_compute=dp.get_precision('Account'), required=False)
    amount = fields.Float(string="Montant de la pénalité", digits_compute=dp.get_precision('Account'), required=False, compute='_calculate_amount')
    total_days = fields.Integer(string="Total jours", required=False)
    penalty_rate = fields.Float(string="Taux pénalité", digits_compute=dp.get_precision('Account'), required=False, related="penalty_fees_product_id.penalty_rate")

    penalty_move_line_ids = fields.One2many(comodel_name="penalty.move.line", inverse_name="penalty_fees_wizard_id", string="Depuis un bon de réception", required=False)
    penalty_purchase_line_ids = fields.One2many(comodel_name="penalty.purchase.line", inverse_name="penalty_fees_wizard_id", string="Depuis un bon de commande", required=False)
    penalty_invoice_line_ids = fields.One2many(comodel_name="penalty.invoice.line", inverse_name="penalty_fees_wizard_id", string="Depuis la facture", required=False)



    @api.depends('total_days','penalty_fees_product_id')
    @api.one
    def _calculate_amount(self):
        print "in calculate penalties"
        print "base_amount = ",self.base_amount
        if self.penalty_fees_product_id.penalty_rate <= 0 or self.total_days <= 0:
            self.amount = 0
        else:
            self.amount = ((self.base_amount > 0 and self.base_amount or False * self.penalty_fees_product_id.penalty_rate)/365) * (self.total_days)

    @api.multi
    def action_validate(self):
        account_id = self.penalty_fees_product_id.property_account_expense.id
        if not account_id:
            raise exceptions.ValidationError("Merci de définir un compte de dépenses pour le produit de pénalités ( "+self.penalty_fees_product_id.name+" )")
        #taxes
        account = self.penalty_fees_product_id.property_account_expense
        taxes = self.penalty_fees_product_id.taxes_id or account.tax_ids
        fpos = self.pool.get('account.fiscal.position').browse(self._cr, self._uid, False)
        fp_taxes = fpos.map_tax(taxes)
        #taxes
        line_vals = {
            'name': self.penalty_fees_product_id.name,
            'account_id': account_id,
            'product_id': self.penalty_fees_product_id.id,
            'quantity': 1,
            'price_unit': self.amount > 0 and (self.amount)*-1 or 0.00,
            'uos_id': self.penalty_fees_product_id.uom_id.id,
            'account_analytic_id': False,
            'invoice_id': self.invoice_id.id,
            'invoice_line_tax_id':[(6, 0, fp_taxes.ids)],
                    }
        self.pool.get("account.invoice.line").create(self._cr, self._uid, line_vals)
        return True


supplier_penalty_fees_wizard()

class penalty_move_line(models.TransientModel):
    _name = 'penalty.move.line'

    @api.onchange('planned_date','reception_date')
    def _calculate_diff(self):
        print "qsdqsdazeazaeffffffff"
        if self.planned_date and self.reception_date:
            delay_days_count = rrule.rrule(rrule.DAILY, dtstart=parser.parse(self.planned_date), until=parser.parse(self.reception_date)).count()-1
            print "delay_days_count =",delay_days_count
            if delay_days_count > 0:
                self.diff = delay_days_count
            else:
                self.diff = 0

    penalty_fees_wizard_id = fields.Many2one(comodel_name="supplier.penalty.fees.wizard", string="Assistant de pénalités", required=False)
    invoice_qty = fields.Float(string="Q.T/FCT", digits_compute=dp.get_precision('Account'), required=False)
    move_id = fields.Many2one(comodel_name="stock.move", string="Mouvement BR", required=False)
    product_name = fields.Char(string="Article BR", required=False, )
    picking_name = fields.Char(string="Bon de réception", required=False, )
    received_qty = fields.Float(string="Q.T/BR", digits_compute=dp.get_precision('Account'), required=False)
    planned_date = fields.Date(string="Date prévue", required=False)
    reception_date = fields.Date(string="Date de réception", required=False)
    diff = fields.Integer(string="Jours", required=False, )

penalty_move_line()


class penalty_purchase_line(models.TransientModel):
    _name = 'penalty.purchase.line'

    penalty_fees_wizard_id = fields.Many2one(comodel_name="supplier.penalty.fees.wizard", string="Assistant de pénalités", required=False)
    invoice_qty = fields.Float(string="Q.T/FCT", digits_compute=dp.get_precision('Account'), required=False)
    purchase_line_id = fields.Many2one(comodel_name="purchase.order.line", string="Article BC", required=False)
    purchase_order_name = fields.Char(string="", required=False,)
    purchased_qty = fields.Float(string="Q.T/BC", digits_compute=dp.get_precision('Account'), required=False)
    planned_date = fields.Date(string="Date prévue", required=False)
    reception_date = fields.Date(string="Date de réception", required=False, default=fields.date.today())
    diff = fields.Integer(string="Jours", required=False, )

penalty_purchase_line()


class penalty_invoice_line(models.TransientModel):
    _name = 'penalty.invoice.line'

    penalty_fees_wizard_id = fields.Many2one(comodel_name="supplier.penalty.fees.wizard", string="Assistant de pénalités", required=False)
    invoice_line_id = fields.Many2one(comodel_name="account.invoice.line", string="Article", required=False)
    invoice_qty = fields.Float(string="Q.T", digits_compute=dp.get_precision('Account'), required=False)
    planned_date = fields.Date(string="Date prévue", required=False, default=fields.date.today())
    reception_date = fields.Date(string="Date de réception", required=False, default=fields.date.today())
    diff = fields.Integer(string="Jours", required=False, )

penalty_invoice_line()