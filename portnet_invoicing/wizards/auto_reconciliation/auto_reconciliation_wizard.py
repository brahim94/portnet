# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp import api, fields, models, exceptions, _
import base64
import csv
import time
from datetime import datetime
from sys import exc_info
from traceback import format_exception
from dateutil import parser, rrule, relativedelta
from openerp.exceptions import Warning
import tempfile
import logging
import os

class reconciled_csv_aml(models.Model):
    _name = 'reconciled.csv.aml'

    @api.depends('aml_ids')
    @api.one
    def _check_to_reconcile(self):
        value = 0
        debit=0
        credit=0
        for line in self.aml_ids :
            if line.aml_account.parent_id.code in ('3421','4411') :
                debit+=line.aml_debit
                credit+=line.aml_credit
        if debit==credit :
            self.to_rec=True

        else :
            self.to_rec=False

    # def _search_to_rec(self,operator,value):
    #     print "operatoooor",operator, value
    #     domain=[('to_rec',operator,value)]
    #     return domain


    aml_ids = fields.One2many(comodel_name="reconciled.csv.aml.line", inverse_name="reconciled_csv_aml_id",string="Ecritures comptable", required=False)
    reconcile_ref = fields.Char(string="Ref.lettrage", required=False)
    to_rec= fields.Boolean(string="Soldé",compute="_check_to_reconcile",store=True)


    @api.multi
    def load_csv_aml(self,aml_data,aml_fname,reconcile=False):
        if not reconcile :
            self._cr.execute("delete from reconciled_csv_aml_line")
            self._cr.execute("delete from reconciled_csv_aml")
            time_start = time.time()
            filepath = tempfile.gettempdir()+'/'+aml_fname
            f = open(filepath,'wb')
            data=base64.decodestring(aml_data)
            f.write(data)
            f.close()
            csvfile=open(filepath)
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)
            i=0
            group_by_ref=[]
            for line in reader:
                #print "LINE",line
                if line[1] :
                    if line[1] not in group_by_ref :
                        #req1="insert into reconciled_csv_aml(reconcile_ref) values ('%s')  RETURNING id "%(line[1])
                        rec_id=self.create({'reconcile_ref':line[1]})
                        req2="insert into reconciled_csv_aml_line(aml_id,reconciled_csv_aml_id) values (%s,'%s') "%(line[0],rec_id.id)
                        self._cr.execute(req2)
                        group_by_ref.append(line[1])
                    else :
                        request="select id from reconciled_csv_aml where reconcile_ref='%s'  "%(line[1])
                        self._cr.execute(request)
                        res_id = [x[0] for x in self._cr.fetchall()]
                        req2="insert into reconciled_csv_aml_line(aml_id,reconciled_csv_aml_id) values (%s,'%s') "%(line[0],res_id[0])
                        self._cr.execute(req2)
                print "iteration",i,line[0],line[1]
                i+=1
            print "---------------------------------CSV LOADED---------------"
        else :
            account_move_line_obj = self.pool.get('account.move.line')
            request="""select b.id
                            from reconciled_csv_aml_line  a , reconciled_csv_aml b, account_account aa  , account_move_line aml
                            where a.reconciled_csv_aml_id=b.id AND
                                  a.aml_id=aml.id AND aml.account_id=aa.id
                                  and ( aa.code like '3421%' or aa.code like '4411%')
                              group by b.id
                            having sum(aml.debit)-sum(aml.credit)=0"""

            self._cr.execute(request)
            results = [x[0] for x in self._cr.fetchall()]
            print "----------Ref lettrage à traitre : ",len(results)
            j=0
            k=0
            for rec in results :
                print "itération",j,rec
                for code in ['3421','4411'] :
                    req="""select a.aml_id
                                from reconciled_csv_aml_line  a , reconciled_csv_aml b, account_account aa ,account_move_line aml
                                where a.reconciled_csv_aml_id=b.id  and a.aml_id=aml.id and aml.account_id=aa.id
                                and b.id="""+str(rec)+"""  and aa.code like '""" + code+ """%' """
                    self._cr.execute(req)
                    move_ids= [x[0] for x in self._cr.fetchall()]
                    if len (move_ids)>1 :
                                print "lettrage",k
                                account_move_line_obj.reconcile_old_lines(self._cr, self._uid,move_ids,'partner',False,'auto' ,context=self._context)
                                k+=1
                j+=1
            print "INDICATEUR : ligne %s , lettrage %s"%(len(results),k)
        return {}
class reconciled_csv_aml_line(models.Model):
    _name = 'reconciled.csv.aml.line'

    reconciled_csv_aml_id = fields.Many2one(comodel_name="reconciled.csv.aml", string="Réf.Lettrage")
    aml_id = fields.Many2one(comodel_name="account.move.line", string="Ecriture comptable ID")
    aml_account = fields.Many2one(comodel_name="account.account", string="Compte", related="aml_id.account_id")
    aml_debit=fields.Float( string="Débit", related="aml_id.debit")
    aml_credit=fields.Float(string="Crédit", related="aml_id.credit")
    aml_reconcile_id= fields.Many2one(comodel_name="account.move.reconcile", string="Ref lettrage", related="aml_id.reconcile_id")
    aml_journal=fields.Many2one(comodel_name="account.journal", string="Journal", related="aml_id.journal_id")


class auto_reconciliation_wizard(models.TransientModel):
    _name = 'auto.reconciliation.wizard'

    date_from=fields.Date(string="Date début")
    date_to = fields.Date(string="Date fin")
    type = fields.Selection(string="Type", selection=[('from_csv', "Par import csv"),('all_accounts', 'Tous les comptes'),('account', 'Par compte'), ('partner', 'Par tier'), ], required=True,default='partner')
    account_id = fields.Many2one(comodel_name="account.account", string="Compte")
    period_ids = fields.Many2many(comodel_name="account.period", relation="auto_reconcile_period_rel", column1="wizard_id", column2="period_id", string="Périodes", )
    filter = fields.Selection(string="Filter", selection=[('none','Sans filtre'),('date', 'Date'), ('period', 'Période'), ], required=False,default='none' )
    aml_data = fields.Binary(string='File', required=False)
    aml_fname = fields.Char(string='Filename')
    reconcile = fields.Boolean(string='Lettrer',default=False)

    @api.multi
    def action_auto_reconcile(self):
        if self.type=='from_csv':
            return self.env['reconciled.csv.aml'].load_csv_aml(self.aml_data,self.aml_fname,self.reconcile)
        print "fIIIIIIIIIn csv lettrage"
        where=False
        group_by=False
        if self.type=='partner':
            print "=========tier traitement================="
            select="select aml.partner_id, sum(aml.credit),sum(aml.debit) from account_move_line as aml, res_partner as part "
            where=""" where aml.partner_id = part.id  and
                part.is_company = true and
                (aml.reconcile_id IS NULL AND aml.reconcile_partial_id IS NULL) and
                aml.account_id =%s """%(str(self.account_id.id))
            group_by="group by aml.partner_id  having sum(aml.credit) - sum(aml.debit) = 0"
            # where traitement
            if self.filter=='date':
                where=where+ " and aml.date is not null and  aml.date<='"+str(self.date_to)+"' and aml.date>='"+str(self.date_from)+"'"
            if self.filter=='period':
                if len(self.period_ids.ids)==1:
                    where=where+ "and period_id = %s"%((self.period_ids.ids[0]))
                if len(self.period_ids.ids)>1:
                     where=where+ "and period_id in %s "%(str(tuple(self.period_ids.ids)))

            request=select+where+group_by
            self._cr.execute(request)
            res_ids = [x[0] for x in self._cr.fetchall()]
            print "Results ",len(res_ids)
            i= 1
            select="select aml.id from account_move_line aml , res_partner part  "
            for line_id in res_ids:
                where_req=where
                print i
                where_req=where_req+ " and partner_id=%s "%(line_id)
                request=select+where_req
                #print request
                self._cr.execute(request)
                move_line_ids = [x[0] for x in self._cr.fetchall()]
                print move_line_ids
                #raise Warning("stop")
                account_move_line_obj = self.pool.get('account.move.line')
                context = self._context.copy()
                if self._context.copy() is None:
                    context = {}
                account_move_line_obj.reconcile_old_lines(self._cr, self._uid, move_line_ids, self.type,line_id,'auto' ,context=context)
                i+=1
        # compte traitement
        if self.type=='account':
            select="select aml.account_id, sum(aml.credit),sum(aml.debit) from account_move_line as aml "
            where=""" where (aml.reconcile_id IS NULL AND aml.reconcile_partial_id IS NULL) and
                aml.account_id =%s """%(str(self.account_id.id))
            group_by="group by aml.account_id  having sum(aml.credit) - sum(aml.debit) = 0"
            # where traitement
            if self.filter=='date':
                where=where+ " and aml.date is not null and  aml.date<='"+str(self.date_to)+"' and aml.date>='"+str(self.date_from)+"'"
            if self.filter=='period':
                if len(self.period_ids.ids)==1:
                    where=where+ "and period_id = %s"%((self.period_ids.ids[0]))
                if len(self.period_ids.ids)>1:
                     where=where+ "and period_id in %s "%(str(tuple(self.period_ids.ids)))

            request=select+where+group_by
            self._cr.execute(request)
            res_ids = [x[0] for x in self._cr.fetchall()]
            print "Results ",len(res_ids)
            i= 1
            select="select aml.id from account_move_line aml  "
            for line_id in res_ids:
                print i
                request=select+where
                self._cr.execute(request)
                move_line_ids = [x[0] for x in self._cr.fetchall()]
                print move_line_ids
                account_move_line_obj = self.pool.get('account.move.line')
                context = self._context.copy()
                if self._context.copy() is None:
                    context = {}
                account_move_line_obj.reconcile_old_lines(self._cr, self._uid, move_line_ids, self.type,line_id,'auto' ,context=context)
                i+=1
        if self.type=='all_accounts':
            select="select aml.account_id, sum(aml.credit),sum(aml.debit) from account_move_line as aml  "
            where=""" where (aml.reconcile_id IS NULL AND aml.reconcile_partial_id IS NULL)
                 """
            group_by="group by aml.account_id  having sum(aml.credit) - sum(aml.debit) = 0"
            # where traitement
            if self.filter=='date':
                where=where+ " and aml.date is not null and  aml.date<='"+str(self.date_to)+"' and aml.date>='"+str(self.date_from)+"'"
            if self.filter=='period':
                if len(self.period_ids.ids)==1:
                    where=where+ "and period_id = %s"%((self.period_ids.ids[0]))
                if len(self.period_ids.ids)>1:
                     where=where+ "and period_id in %s "%(str(tuple(self.period_ids.ids)))

            request=select+where+group_by
            self._cr.execute(request)
            res_ids = [x[0] for x in self._cr.fetchall()]
            print "Results ",len(res_ids)
            i= 1
            select="select aml.id from account_move_line aml "
            for line_id in res_ids:
                where_req=where
                print "itération",i,line_id
                where_req=where_req+ " and account_id=%s "%(line_id)
                request=select+where_req
                self._cr.execute(request)
                move_line_ids = [x[0] for x in self._cr.fetchall()]
                print move_line_ids
                account_move_line_obj = self.pool.get('account.move.line')
                context = self._context.copy()
                if self._context.copy() is None:
                    context = {}
                account_move_line_obj.reconcile_old_lines(self._cr, self._uid, move_line_ids, self.type,line_id,'auto' ,context=context)
                i+=1

        return True

auto_reconciliation_wizard()