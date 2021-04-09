# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _, tools
import datetime
import os
from datetime import timedelta
from dateutil import parser


class budget_tri_suivi_wizard(models.TransientModel):
    _name = 'budget.tri.suivi.wizard'


    period1 = fields.Many2one(comodel_name="account.period", string="De")
    period2 = fields.Many2one(comodel_name="account.period", string="A")

    @api.multi
    def _prac_amt(self, line_id, date_from, date_to, commitment=False):
        res = {}
        result = 0.0
        context = self._context or {}
        line = self.env['crossovered.budget.lines'].browse(line_id)
        #journal_clause = " AND aj.type %s 'general'" % (commitment and '=' or '<>')
        journal_clause = " AND aj.commitment_journal %s true" % (commitment and 'is' or 'is not')
        acc_ids = [x.id for x in line.general_budget_id.account_ids]
        if not acc_ids:
            raise Warning(_("The Budget '%s' has no accounts!") % tools.ustr(line.general_budget_id.name))
        if line.id:
            sql_string, sql_args = line._get_sql_query(journal_clause, line.id,
                                                       date_from, date_to, acc_ids)
            print "sql_string prac suivi =",sql_string
            self._cr.execute(sql_string, sql_args)
            result = self._cr.fetchone()[0]
        if result is None:
            result = 0.0
        return result

    @api.multi
    def action_gen(self):
        if self.period2.fiscalyear_id.id != self.period1.fiscalyear_id.id :
            raise exceptions.ValidationError('Merci de selectionner des périodes ayant le mêmme exercice comptable')
        if self.period1 != self.period2 and self.period2.date_start < self.period1.date_stop  :
            raise exceptions.ValidationError('Intervalle de périodes incorrecte')
        self._cr.execute("DELETE FROM quarterly_indicators_monitoring_budget_report")
        date_start = self.period1.date_start
        date_stop = self.period2.date_stop
        where=" where (date_to >= '%s'  and date_from <='%s' )"%(date_start,date_stop)
        self._cr.execute("SELECT id,name,planned_amount FROM crossovered_budget_lines" + where)
        budget_lines = self._cr.dictfetchall()
        for line in budget_lines:
            vals={
                'line_id':line['id'],
                 'rubrique':line['name'],
                  'name':str(self.period1.name)+" - "+str(self.period2.name),
                  'initial_credit':line['planned_amount'],
                  'engagement':self._prac_amt(line['id'],date_start,date_stop,commitment=True)
                  }
            try:
                taux = (vals['engagement']/vals['initial_credit'])*100
            except:
                taux = 0.00
            vals['taux'] = taux
            self.env['quarterly.indicators.monitoring.budget.report'].create(vals)

        return {
            'name':_("Indicateurs trimestriels de suivi du budget"),
            'view_mode': 'tree',
            'view_type': 'form',
            'res_model': 'quarterly.indicators.monitoring.budget.report',
            'type': 'ir.actions.act_window',
            'domain': '[]',
            #'context':"{'search_default_group_by_rubrique': True,}"
            }


budget_tri_suivi_wizard()