# -*- coding: utf-8 -*-

from openerp.tools.translate import _
from openerp import models, fields,  api, _
import os, os.path ,glob
import csv
import tempfile
from datetime import datetime
import time
from openerp.exceptions import except_orm, Warning, RedirectWarning
import logging
_logger = logging.getLogger(__name__)

class etebac_amount_coding(models.Model):
    _name="etebac.amount.coding"

    code=fields.Char(string="Codification ETEBAC",required=True,size=1)
    value=fields.Char(string="Valeur Dernier Chiffre des Centimes",required=True,size=1)
    sign=fields.Selection([('+','+'),('-','-')],string="Signe Opération",default='+')
    positional_id=fields.Many2one(comodel_name='positional.file',string="Fichier positionnel")

class etebac_file(models.Model):
    _name="etebac.file"

    name=fields.Char(string="Nom",required=True)
    state=fields.Selection([('loaded','Chargé'),('exception','Exception')],string="Statu")
    bank_statement_id=fields.Many2one(comodel_name='account.bank.statement',string="Relevé bancaire")


class positional_file(models.Model) :

    _name="positional.file"

    name=fields.Char(string="Nom d'enregistrement")
    code=fields.Char(string="Code d'enregistrement",required=True,size=2)
    size=fields.Integer(string="Longeur Totale",required=True)
    field_ids=fields.One2many(comodel_name='positional.file.line',inverse_name="file_id",string="Champs")
    state=fields.Selection([('draft','Brouillon'),('confirmed','Confirmé')],string="Statu",readonly=True,default='draft')
    amount_coding_ids=fields.One2many(comodel_name='etebac.amount.coding',inverse_name="positional_id",string="Table correspondance")

    @api.constrains('code')
    def _check_code(self):
      res=self.search( [('code','=',self.code)] )
      if len(res) > 1:
        raise Warning("Le code d'enregistrement doit être unique")

    @api.multi
    def set_to_confirmed(self):
        res=[]
        for line in self.field_ids :
            if line.related:
                    res.append(line.related)
        res=set(res)
        if self.code=="04":
            list=set(['label','amount','date','bank','ref','type'])
        if self.code in ("01","07") :
              list=set(['amount','date'])
        if len(list-res)!=0:
                 raise except_orm(_("Vous n'avez pas configuré tous les champs relation pour ce type"),_(list))
        self.state='confirmed'

    @api.multi
    def  set_to_draft (self):
        self.state='draft'

    def _get_amount(self,amount,positional_id):
        print '1-amount -1',amount
        indice=False
        amount=list(amount)
        #recuperation de l'indice à partir duquel le montant commence
        for l in amount :
            if l != '0':
                indice=amount.index(l)
                break
        if indice :
            res=''.join(map(str, amount[indice:-1]))
        #traitement de l'encodage du montant à partir de la correspondance liée au type de l'enregistrement
        amount_coding_id=positional_id.amount_coding_ids.search([('code','=',amount[13]),('positional_id','=',positional_id.id)])
        print "2-amount_coding_id -2",amount_coding_id
        if amount_coding_id :
            sign= 1 if amount_coding_id.sign=='+' else -1
            res=float(str(res+amount_coding_id.value))*sign
            print "3-res-3",res, round(res/100,2)
            return round(res/100,2)


    def _load_positional_file(self,filepath,journal_id,bank_id=False) :
          '''
          cette fonction charge quotidiennement les fichiers ETEBAC3 dans des revelvés bancaires
          :param filepath:
          :param journal_id:
          :param bank_id:
          :return:
          '''
          bank_statement=self.env["account.bank.statement"]
          bank_statement_line=self.env["account.bank.statement.line"]
          account_period=self.env["account.period"]
          exception_obj=self.env['report.exception']
          exception_type='etebac'
          statement_vals={}
          statement_lines=[]
          file=open(filepath)
          filename=os.path.basename(filepath)
          _logger.warning('demarrage de la lecture du releve')
          for file_line in file:
              positional_id=self.search([('code','=',file_line[:2]),('state','=','confirmed')])
              if not positional_id :
                  code='config_etebac_error_'+str((file_line[:2]))
                  output="Il n'existe pas de configuration pour le type d'enregistrement %s"%(file_line[:2])
                  exception_obj.set_exception(code,output,exception_type)
              if positional_id.code=='01' :
                  print "---------------------------------------01-------------------------------------"
                  res={}
                  for line in positional_id.field_ids :
                      if line.related in ('amount','date') :
                          position=int(line.position)-1
                          length=int(line.length)
                          res[str(line.related)]=file_line[position:position+length]
                  try :
                        date="20"+res['date'][4:]+"-"+res['date'][2:4]+"-"+res['date'][:2]
                        last_balance_date=datetime.strptime(date,"%Y-%m-%d")
                        if not bank_statement.search([('last_balance_date','=',last_balance_date)]) :
                             balance_start=self._get_amount(res['amount'],positional_id)
                             statement_vals['last_balance_date']=last_balance_date
                             statement_vals['balance_start']=balance_start

                        else : break
                  except :
                       code='config_error'
                       output="La date ou le montant ne sont pas configurés au niveau du record type 01"
                       exception_obj.set_exception(code,output,exception_type)
                       break
              if positional_id.code=='04' :
                  print "---------------------------------------04-------------------------------------"
                  res={}
                  for line in positional_id.field_ids :
                      if line.related in('label','ref','bank','amount','date','type') :
                          position=int(line.position)-1
                          length=int(line.length)
                          res[str(line.related)]=file_line[position:position+length]
                  try :
                      date="20"+res['date'][4:]+"-"+res['date'][2:4]+"-"+res['date'][:2]
                      date=datetime.strptime(date,"%Y-%m-%d")
                  except :
                       code='config_date_error'
                       output="La date n'est pas configuré au niveau du record type 04"
                       exception_obj.set_exception(code,output,exception_type)
                       continue
                  try :

                      amount=self._get_amount(res['amount'],positional_id)
                      vals={
                                    'date':date,
                                    'amount':amount,
                                    'name':res['label'].rstrip(),
                      }
                      print "4- operation type -4",res['type'],len(res['type'])
                      if amount >= 0 :
                          domain=[('code','=',res['type']),('type','=','C')]
                      else :
                          domain=[('code','=',res['type']),('type','=','D')]
                      operation_id=self.env['bank.operation'].search(domain)
                      if operation_id :
                          print '5- operation code -5 %s \n'%operation_id.code
                          vals['bank_operation_id']=operation_id.id

                      statement_lines.append(vals)
                  except:
                      code='config_amount_error %s'%file_line
                      output="Le montant n'est pas configuré au niveau du record type 04 :%s "%file_line
                      exception_obj.set_exception(code,output,exception_type)
                      continue
              if positional_id.code=='07' :
                  print "---------------------------------------07-------------------------------------"
                  res={}
                  for line in positional_id.field_ids :
                      if line.related in ('amount','date') :
                          position=int(line.position)-1
                          length=int(line.length)
                          res[str(line.related)]=file_line[position:position+length]
                  try :
                        date="20"+res['date'][4:]+"-"+res['date'][2:4]+"-"+res['date'][:2]
                        balance_date=datetime.strptime(date,"%Y-%m-%d")
                        statement_vals['date']=balance_date
                        period=account_period.find(balance_date)
                        if not period :
                          code='period_error_'+str(date)
                          output="Il n'existe une période fiscale pour la date %s "%(date)
                          exception_obj.set_exception(code,output,exception_type)
                          break
                        statement_vals['period_id']=period.id
                  except :
                          code='congif_date_error'
                          output="La date n'est pas configuré au niveau du record type 07 "
                          exception_obj.set_exception(code,output,exception_type)
                          break
                  try :
                          balance_end_real=self._get_amount(res['amount'],positional_id)
                          statement_vals['balance_end_real']=balance_end_real
                  except :
                          code='balance_end_real_error'
                          output="Le montant n'est pas configuré au niveau du record type 07 "
                          exception_obj.set_exception(code,output,exception_type)
                          break
          if statement_vals :
              statement_vals['bank_id']=bank_id
              statement_vals['journal_id']=journal_id
              statement_id=bank_statement.create(statement_vals)
              for line in statement_lines :
                  line['statement_id']=statement_id.id
                  bank_statement_line.create(line)
              self.env['etebac.file'].create({'name':filename,'state':'loaded','bank_statement_id':statement_id.id})
              _logger.warning("confirmation du releve")
              try :
                #print "hhhh"
                statement_id.button_confirm(context=None,cron=True)

              except :
                  code='statement_confirm_error'
                  output="Le relevé bancaire %s n'a pas été confirmé"%(statement_id.name)
                  exception_obj.set_exception(code,output,exception_type)
              try :
                  if statement_id.state =='confirm' :

                      bank_reconcile_vals={
                                            'fiscalyear_id':statement_id.period_id.fiscalyear_id.id,
                                            'journal_id':statement_id.journal_id.id,
                                            'periode_id': statement_id.period_id.id,
                                           # 'account_bank_statement_id':statement_id.id,
                                            'account_id': statement_id.account_id.id
                                        }
                      _logger.warning("releve confirme : creation du rapprochement")
                      reconcile_bank_id=self.env['reconcile.bank'].create(bank_reconcile_vals)
                      #reconcile_bank_id.onchange_bank_statement_id()
                      #reconcile_bank_id.onchange_account_id()
                      _logger.warning("confirmation du rapprochement")
                      reconcile_bank_id.action_confirm()
                      _logger.warning("rapprochement en cours ...")
                      reconcile_bank_id.auto_reconcile_action(cron=True)
                      _logger.warning("rapprochement terminé !")
              except :
                  code='bank_reconcile_create_error'
                  output="Le systéme n'a pas pu crée un traitement rapprochement banciare pour le  relevé %s (non confirmé)"%(statement_id.name)
                  exception_obj.set_exception(code,output,exception_type)


          return True

class positional_file_line(models.Model) :

    _name="positional.file.line"

    _order ="position"

    column=fields.Char(string="Champ")
    data_type=fields.Char(string="Type de données")
    position=fields.Integer(string="Position début")
    length=fields.Integer(string="Longueur")
    note=fields.Char(string="Note")
    required=fields.Boolean(string="Obligatoire")
    file_id=fields.Many2one(comodel_name='positional.file',string="Fichier positionnel")
    related=fields.Selection([('label','Libellé'),('ref','Réf Opération'),('bank','Banque'),('amount','Montant'),('date','Date'),('type','Type Opération')],string="Champ relation")

    @api.constrains('related')
    def _check_code(self):
      if self.related :
          res=self.search( [('related','=',self.related),('file_id','=',self.file_id.id)] )
          if len(res) > 1:
            raise Warning("La relation doit être unique par champ ")

