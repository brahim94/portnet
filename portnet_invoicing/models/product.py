# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp


class product_product(models.Model):
    _inherit = 'product.product'

    @api.one
    @api.constrains('default_code')
    def _check_code_portnet(self):
      res=self.search( [('default_code','=',self.default_code)] )
      if len(res) > 1:
        raise Warning("Le code portnet est unique par produit")


product_product()


class product_template(models.Model):
    _inherit = 'product.template'

    is_subscription = fields.Boolean(string="Abonnement")
    periodicity_id = fields.Many2one(comodel_name="res.periodicity", string="Périodicité",required=False)
    penalty_fees = fields.Boolean(string="Pénalités client")
    supplier_penalty_fees = fields.Boolean(string="Pénalités fournisseur")
    penalty_rate = fields.Float(string="Taux pénalité (10% => 0.1)", digits_compute=dp.get_precision('Account'), required=False)
    is_service = fields.Boolean(string="Service")

product_template()


