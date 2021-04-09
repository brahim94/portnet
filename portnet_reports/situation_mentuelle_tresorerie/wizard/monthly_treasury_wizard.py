# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os
from datetime import timedelta
from dateutil import parser

class monthly_treasury_wizard(models.TransientModel):
    _name = 'monthly.treasury.wizard'

    recalculate = fields.Boolean(string="Recalculer le plan de trésorerie avant génération du suivi")
    period_ids = fields.Many2many(comodel_name="account.period", relation="monthly_treasury_period_rel", column1="wizard_id", column2="period_id", string="Périodes", )

    @api.multi
    def action_gen(self):
        if not self.period_ids :
            raise exceptions.ValidationError('Aucune période selectionnée')
        self._cr.execute("DELETE FROM monthly_monitoring_treasury_report")
        for period in self.period_ids:
            date_start = period.date_start
            date_stop = period.date_stop
            treasury = self.env['account.treasury.forecast'].search([('start_date','<=',date_start),('end_date','>=',date_stop)])
            if not treasury:
                raise exceptions.ValidationError('Aucun plan de trésorerie trouvé pour la période '+str(period.name))
            treasury_categs = self.env['treasury.categ'].search([('is_active','=',True),('sum','=',False),('is_root','=',False)])
            for t_categ in treasury_categs:
                vals = {'period_id':period.id,
                        'name':t_categ.name,
                        'initial_solde':treasury.start_amount,
                        'encais':0.00,
                        'dencais':0.00,
                        'final_solde':0.00
                            }
                for acc in t_categ.account_ids:
                    amount_column = t_categ.type == 'd' and 'debit' or 'credit'
                    reconciled_entries_only = acc.treasury_reconcile
                    # Entries from account moves
                    req = "SELECT SUM("+amount_column+") AS amount  " \
                          " FROM account_move_line as aml " \
                          " WHERE date BETWEEN '"+str(date_start)+"' AND '"+str(date_stop)+"' " \
                          " AND account_id = "+str(acc.id)+"  " \
                          " AND "+amount_column+" > 0 "
                    if acc.treasury_reconcile:
                        req+=" AND (reconcile_id IS NOT NULL OR reconcile_partial_id IS NOT NULL) "
                    self._cr.execute(req)
                    dict_res = self._cr.dictfetchall()
                    for dict in dict_res:
                        vals['encais'] += t_categ.type == 'r' and dict['amount'] or 0.00
                        vals['dencais'] += t_categ.type == 'd' and dict['amount'] or 0.00
                    req = "SELECT SUM("+amount_column+") AS initial_amount  " \
                          " FROM account_move_line as aml " \
                          " WHERE date BETWEEN '"+str(treasury.start_date)+"' AND '"+str(parser.parse(date_start)+timedelta(days=-1))+"' " \
                          " AND account_id = "+str(acc.id)+"  " \
                          " AND "+amount_column+" > 0 "
                    if acc.treasury_reconcile:
                        req+=" AND (reconcile_id IS NOT NULL OR reconcile_partial_id IS NOT NULL) "
                    self._cr.execute(req)
                    dict_res = self._cr.dictfetchall()
                    for dict in dict_res:
                        plus_amount = dict['initial_amount'] and dict['initial_amount'] or 0.00
                        vals['initial_solde']+=plus_amount
                        vals['final_solde'] = (vals['encais'] > 0 and vals['encais'] or vals['dencais'])+(vals['initial_solde'])
                self.env['monthly.monitoring.treasury.report'].create(vals)
        return {
            'name':_("Suivi mensuel de la trésorerie"),
            'view_mode': 'tree',
            'view_type': 'form',
            'res_model': 'monthly.monitoring.treasury.report',
            'type': 'ir.actions.act_window',
            'domain': '[]',
            'context':"{'search_default_group_by_period_id': True,}"
            }

    # @api.multi
    # def action_gen(self):
    #     if not self.period_ids :
    #         raise exceptions.ValidationError('Aucune période selectionnée')
    #     self._cr.execute("DELETE FROM monthly_monitoring_treasury_report")
    #     recalculated_treasury_ids = []
    #     for period in self.period_ids:
    #         date_start = period.date_start
    #         date_stop = period.date_stop
    #         treasury = self.env['account.treasury.forecast'].search([('start_date','<=',date_start),('end_date','>=',date_stop)])
    #         if not treasury:
    #             raise exceptions.ValidationError('Aucun plan de trésorerie trouvé pour la période '+str(period.name))
    #         if self.recalculate and treasury.id not in recalculated_treasury_ids:
    #             print "calculating"
    #             treasury.get_entries()
    #             recalculated_treasury_ids.append(treasury.id)
    #         self._cr.execute("SELECT treasury_categ_id FROM treasury_entry WHERE treasury_id = "+str(treasury.id)+" AND date between '"+str(date_start)+"' AND '"+str(date_stop)+"' group by treasury_categ_id")
    #         treasury_categs = self._cr.dictfetchall()
    #         for t_categ in treasury_categs:
    #             req ="SELECT SUM(amount) as amount FROM treasury_entry " \
    #                  " WHERE treasury_id = "+str(treasury.id)+" " \
    #                  " AND treasury_categ_id = "+str(t_categ['treasury_categ_id'])+" " \
    #                  " AND date BETWEEN '"+str(date_start)+"' AND '"+str(date_stop)+"' "
    #             self._cr.execute(req)
    #             dict_res = self._cr.dictfetchall()
    #             t_categ_record = self.env['treasury.categ'].browse(t_categ['treasury_categ_id'])
    #             vals = {'period_id':period.id,
    #                     'name':t_categ_record and t_categ_record.name or '',
    #                     'initial_solde':treasury.start_amount
    #                     }
    #             for dict in dict_res:
    #                 vals['encais'] = t_categ_record.type == 'r' and dict['amount'] or 0.00
    #                 vals['dencais'] = t_categ_record.type == 'd' and dict['amount'] or 0.00
    #             req ="SELECT SUM(amount) as amount FROM treasury_entry " \
    #              " WHERE treasury_id = "+str(treasury.id)+" " \
    #              " AND treasury_categ_id = "+str(t_categ['treasury_categ_id'])+" " \
    #              " AND date BETWEEN '"+str(treasury.start_date)+"' AND '"+str(parser.parse(date_start)+timedelta(days=-1))+"' "
    #             self._cr.execute(req)
    #             dict_res = self._cr.dictfetchall()
    #             for dict in dict_res:
    #                 plus_amount = dict['amount'] and dict['amount'] or 0.00
    #                 vals['initial_solde']+=plus_amount
    #                 vals['final_solde'] = (vals['encais'] > 0 and vals['encais'] or vals['dencais'])+(vals['initial_solde'])
    #             self.env['monthly.monitoring.treasury.report'].create(vals)
    #     return {
    #         'name':_("Suivi mensuel de la trésorerie"),
    #         'view_mode': 'tree',
    #         'view_type': 'form',
    #         'res_model': 'monthly.monitoring.treasury.report',
    #         'type': 'ir.actions.act_window',
    #         'domain': '[]',
    #         'context':"{'search_default_group_by_period_id': True,}"
    #         }


monthly_treasury_wizard()