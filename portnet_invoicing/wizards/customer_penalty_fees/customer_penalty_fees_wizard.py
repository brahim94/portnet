# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from dateutil import parser, rrule, relativedelta
from datetime import date, timedelta

class customer_penalty_fees_wizard(models.TransientModel):
    _name = 'customer.penalty.fees.wizard'

    invoice_id = fields.Many2one(comodel_name="account.invoice", string="Facture", required=False)
    penalty_fees_product_id = fields.Many2one(comodel_name="product.product", string="Pénalités à appliquer", required=False, domain=[('penalty_fees','=',True)])
    penalty_rate = fields.Float(string="Taux pénalité", digits_compute=dp.get_precision('Account'), required=False, compute="_get_penalty_rate")
    base_amount = fields.Float(string="Montant facture", digits_compute=dp.get_precision('Account'), required=False)
    amount = fields.Float(string="Montant de la pénalité", digits_compute=dp.get_precision('Account'), required=False, compute="_calculate_amount")
    total_days = fields.Integer(string="Total jours", required=False, compute="_calculate_diff")
    planned_date = fields.Date(string="Date d'échéance", required=False)
    reception_date = fields.Date(string="Date de paiement", required=False, default=fields.date.today())



    @api.depends('planned_date','reception_date')
    @api.one
    def _calculate_diff(self):
        if self.planned_date and self.reception_date:
            delay_days_count = rrule.rrule(rrule.DAILY, dtstart=parser.parse(self.planned_date), until=parser.parse(self.reception_date)).count()-1
            print "delay_days_count =",delay_days_count
            if delay_days_count > 0:
                self.total_days = delay_days_count
            else:
                self.total_days = 0

    @api.depends('total_days','penalty_rate')
    @api.one
    def _calculate_amount(self):
        if self.penalty_rate <= 0 or self.total_days <= 0:
            self.amount = 0
        else:
            print "base_amount =",self.base_amount
            if self.base_amount > 0:
                self.amount = ((self.base_amount*self.penalty_rate)/365) * (self.total_days)
            else:
                raise exceptions.ValidationError("Le montant de la facture doît être supérieur à 0")


    @api.depends('penalty_fees_product_id','invoice_id.partner_id','invoice_id.partner_id.categ_id')
    @api.one
    def _get_penalty_rate(self):
        print "self.invoice_id =",self.invoice_id
        print "self.invoice_id.partner_id =",self.invoice_id.partner_id
        print "self.invoice_id.partner_id.penalty_rate =",self.invoice_id.partner_id.penalty_rate
        if self.invoice_id.partner_id.penalty_rate > 0:
            print "in ifffffffffff"
            self.penalty_rate = self.invoice_id.partner_id.penalty_rate
        elif self.penalty_fees_product_id.penalty_rate > 0:
            self.penalty_rate = self.penalty_fees_product_id and self.penalty_fees_product_id.penalty_rate
        elif self.invoice_id.partner_id.categ_id.penalty_rate > 0:
            self.penalty_rate = self.invoice_id.partner_id.categ_id.penalty_rate


    @api.multi
    def action_validate(self):
        new_invoice= False
        if self.invoice_id.state != 'draft':
            #invoice gen
            if self.invoice_id.partner_id.property_payment_term:
                payment_term_id = self.partner_id.property_payment_term.id
            elif self.invoice_id.partner_id.categ_id and self.invoice_id.partner_id.categ_id.payment_term_id:
                payment_term_id = self.invoice_id.partner_id.categ_id.payment_term_id.id
            else:
                payment_term_id = False

            vals = {
                'origin': self.invoice_id.name,
                'date_invoice': fields.date.today(),
                'user_id': self._uid,
                'partner_id': self.invoice_id.partner_id.id,
                'account_id': self.invoice_id.partner_id.property_account_receivable.id,
                'type': 'out_invoice',
                'company_id': self.env.user.company_id.id,
                'currency_id': self.invoice_id.currency_id.id,
                'pricelist_id':self.invoice_id.pricelist_id and self.invoice_id.pricelist_id.id or False,
                'payment_term':payment_term_id,
                'origin':self.invoice_id.name
                #'partner_bank_id':partner_bank and partner_bank[0].id or False,
                #'journal_id':journal and journal[0].id or False,
            }
            invoice_obj = self.env['account.invoice']
            new_invoice = invoice_obj.create(vals)
            new_invoice.button_reset_taxes()

        account_id = self.penalty_fees_product_id.property_account_income.id
        if not account_id:
            raise exceptions.ValidationError("Merci de définir un compte de revenues pour le produit de pénalités ( "+self.penalty_fees_product_id.name+" )")
        #taxes
        account = self.penalty_fees_product_id.property_account_income
        taxes = self.penalty_fees_product_id.taxes_id or account.tax_ids
        fpos = self.pool.get('account.fiscal.position').browse(self._cr, self._uid, False)
        fp_taxes = fpos.map_tax(taxes)
        #taxes
        line_vals = {
            'name': self.penalty_fees_product_id.name,
            'account_id': account_id,
            'product_id': self.penalty_fees_product_id.id,
            'quantity': 1,
            'price_unit': self.amount > 0 and self.amount or 0.00,
            'uos_id': self.penalty_fees_product_id.uom_id.id,
            'account_analytic_id': False,
            'invoice_id': new_invoice and new_invoice.id or self.invoice_id.id,
            'invoice_line_tax_id':[(6, 0, fp_taxes.ids)],
                    }
        self.env["account.invoice.line"].create(line_vals)
        if new_invoice:
            return {
            'name':_("Factures clients"),
            'view_mode': 'form',
            'view_id': self.env.ref('account.invoice_form').id,
            'view_type': 'form',
            'res_model': 'account.invoice',
            'res_id':new_invoice.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': '[]',
            }
        else:
            return True


customer_penalty_fees_wizard()
