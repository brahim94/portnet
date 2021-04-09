# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os

class fact_encaiss_wizard(models.TransientModel):
    _name = 'fact.encaiss.wizard'

    period_ids = fields.Many2many(comodel_name="account.period", relation="fact_encaiss_period_rel", column1="wizard_id", column2="period_id", string="Périodes", )

    @api.multi
    def action_gen(self):
        if not self.period_ids :
            raise exceptions.ValidationError('Aucune période selectionnée')
        self._cr.execute("DELETE FROM payment_invoice_reporting")
        sql = " select rp.code as code_partner, pp.default_code as code_pres ,ail.name as design_pres ,ai.number as num_invoice , " \
              " ai.amount_untaxed as amount_untaxed ,ai.amount_total as amount_total ,ai.amount_tax as amount_tax ,ail.quantity as quantity , " \
              " ail.price_unit as price_unit ,rp.name as partner_name ,ai.date_invoice as date_invoice, ai.period_id as period_id " \
              " from account_invoice as ai, account_invoice_line as ail, product_product as pp, res_partner as rp " \
              " where ail.invoice_id = ai.id and ail.product_id = pp.id and ai.partner_id = rp.id " \
              " and ai.type='out_invoice'" \
              " and ai.state <> 'draft' "
        if len(self.period_ids.ids)==1:
            sql+= " and ai.period_id = %s"%((self.period_ids.ids[0]))
        if len(self.period_ids.ids)>1:
            sql+= " and ai.period_id in %s "%(str(tuple(self.period_ids.ids)))
        #sql+=" limit 50"
        self._cr.execute(sql)
        result = self._cr.dictfetchall()
        i=0
        for res in result:
            i+=1
            sql =" select aml.id as aml_id, aml.ref as ref_reglement ,aml.name as name_reglement ,aml.debit as debit ,aml.credit as credit, aml.reconcile_id, aml.reconcile_partial_id, aml.reglement_method_id " \
                 " from account_move_line as aml " \
                 " where(  " \
                 " (aml.reconcile_id in (select reconcile_id from account_move_line where ref='"+str(res['num_invoice'])+"' and reconcile_id is not null)) " \
                 " OR  " \
                 " (aml.reconcile_partial_id in (select reconcile_partial_id from account_move_line where ref='"+str(res['num_invoice'])+"' and reconcile_partial_id is not null)) " \
                 " ) " \
                 " AND aml.credit > 0"
            self._cr.execute(sql)
            aml_result = self._cr.dictfetchall()
            values = {'code_partner':res['code_partner'] and res['code_partner'].replace("'"," ") or " ",
                    'code_pres':res['code_pres'] and res['code_pres'].replace("'"," ") or " ",
                    'design_pres':res['design_pres'] and res['design_pres'].replace("'"," ") or " ",
                    'num_invoice':res['num_invoice'],
                    'amount_untaxed':res['amount_untaxed'],
                    'amount_total':res['amount_total'],
                    'amount_tax':res['amount_tax'],
                    'quantity':res['quantity'],
                    'price_unit':res['price_unit'],
                    'partner_name':res['partner_name'] and res['partner_name'].replace("'"," ") or " ",
                    'date_invoice':res['date_invoice'] ,
                    'period_id':res['period_id'],
                    }
            if aml_result:
                for aml in aml_result:
                    print "reglement"
                    aml_record =self.env['account.move.line'].browse(int(aml['aml_id']))
                    balance = values['amount_total'] - aml['credit']
                    req=" INSERT INTO payment_invoice_reporting(period_id,code_partner,code_pres,design_pres,num_invoice,amount_untaxed,amount_total,amount_tax,quantity,price_unit,partner_name," \
                    "date_invoice,ref_reglement,name_reglement,debit,credit,reconcile_type,balance,date_payment)"
                    if aml['reglement_method_id']:
                        req = req[:-1]
                        req+=",method_id)"
                    req+= " VALUES("+str(values['period_id'])+",'"+str(values['code_partner'])+"','"+str(values['code_pres'])+"','"+str(values['design_pres'])+"','"+str(values['num_invoice'])+"',"
                    req+= str(values['amount_untaxed'])+","+str(values['amount_total'])+","+str(values['amount_tax'])+","+str(values['quantity'])+","+str(values['price_unit'])+","
                    req+= "'"+str(values['partner_name'])+"','"+str(values['date_invoice'])+"'"
                    req+=",'"+str(aml['ref_reglement'])+"','"+str(aml['name_reglement'])+"',"+str(aml['debit'])+","+str(aml['credit'])
                    if aml['reconcile_id']:
                        req+=",'total'"
                    elif aml['reconcile_partial_id']:
                        req+=",'partial'"
                    req+=","+str(balance)
                    if aml_record:
                        req+=",'"+str(aml_record.last_rec_date)+"'"
                    if aml['reglement_method_id']:
                        req+=","+str(aml['reglement_method_id'])
                    req+= ")"
                    self._cr.execute(req)
            else:
                req=" INSERT INTO payment_invoice_reporting(period_id,code_partner,code_pres,design_pres,num_invoice,amount_untaxed,amount_total,amount_tax,quantity,price_unit,partner_name," \
                "date_invoice,ref_reglement,name_reglement,debit,credit,reconcile_type,balance)"
                req+= " VALUES("+str(values['period_id'])+",'"+str(values['code_partner'])+"','"+str(values['code_pres'])+"','"+str(values['design_pres'])+"','"+str(values['num_invoice'])+"',"
                req+= str(values['amount_untaxed'])+","+str(values['amount_total'])+","+str(values['amount_tax'])+","+str(values['quantity'])+","+str(values['price_unit'])+","
                req+= "'"+str(values['partner_name'])+"','"+str(values['date_invoice'])+"'"
                req+=",' ',' ',0.00,0.00,'none',"+str(values['amount_total'])+")"
                self._cr.execute(req)
            print str(i)+" / "+str(len(result))

        return {
            'name':_("Situation globale facturation/encaissements"),
            'view_mode': 'tree',
            'view_type': 'form',
            'res_model': 'payment.invoice.reporting',
            'type': 'ir.actions.act_window',
            'domain': '[]',
            }


fact_encaiss_wizard()