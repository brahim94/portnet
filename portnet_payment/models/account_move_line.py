# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tools.translate import _
from openerp import models, fields,  api, _
import os, os.path ,glob
import csv
import time
from openerp.osv import osv, fields as osvfields
import tempfile
from openerp.exceptions import except_orm, Warning, RedirectWarning

class account_move_line_(osv.osv):
    _inherit = "account.move.line"

    def _invoice(self, cursor, user, ids, name, arg, context=None):
        invoice_obj = self.pool.get('account.invoice')
        res = {}
        for line_id in ids:
            res[line_id] = False
        cursor.execute('SELECT l.id, i.id ' \
                        'FROM account_move_line l, account_invoice i ' \
                        'WHERE l.move_id = i.move_id ' \
                        'AND l.id IN %s',
                        (tuple(ids),))
        invoice_ids = []
        for line_id, invoice_id in cursor.fetchall():
            res[line_id] = invoice_id
            invoice_ids.append(invoice_id)
        invoice_names = {}
        for invoice_id, name in invoice_obj.name_get(cursor, user, invoice_ids, context=context):
            invoice_names[invoice_id] = name
        for line_id in res.keys():
            invoice_id = res[line_id]
            res[line_id] = invoice_id and (invoice_id, invoice_names[invoice_id]) or False
        return res

    def _invoice_search(self, cursor, user, obj, name, args, context=None):
        if not args:
            return []
        invoice_obj = self.pool.get('account.invoice')
        i = 0
        while i < len(args):
            fargs = args[i][0].split('.', 1)
            if len(fargs) > 1:
                args[i] = (fargs[0], 'in', invoice_obj.search(cursor, user,
                    [(fargs[1], args[i][1], args[i][2])]))
                i += 1
                continue
            if isinstance(args[i][2], basestring):
                res_ids = invoice_obj.name_search(cursor, user, args[i][2], [],
                        args[i][1])
                args[i] = (args[i][0], 'in', [x[0] for x in res_ids])
            i += 1
        qu1, qu2 = [], []
        for x in args:
            if x[1] != 'in':
                if (x[2] is False) and (x[1] == '='):
                    qu1.append('(i.id IS NULL)')
                elif (x[2] is False) and (x[1] == '<>' or x[1] == '!='):
                    qu1.append('(i.id IS NOT NULL)')
                else:
                    qu1.append('(i.id %s %s)' % (x[1], '%s'))
                    qu2.append(x[2])
            elif x[1] == 'in':
                if len(x[2]) > 0:
                    qu1.append('(i.id IN (%s))' % (','.join(['%s'] * len(x[2]))))
                    qu2 += x[2]
                else:
                    qu1.append(' (False)')
        if qu1:
            qu1 = ' AND' + ' AND'.join(qu1)
        else:
            qu1 = ''
        cursor.execute('SELECT l.id ' \
                'FROM account_move_line l, account_invoice i ' \
                'WHERE l.move_id = i.move_id ' + qu1, qu2)
        res = cursor.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    _columns = {
        'invoice': osvfields.function(_invoice, string='Invoice',
                                   type='many2one', relation='account.invoice', fnct_search=_invoice_search, store=True),
    }

account_move_line_()

class unprocessed_jplus2(models.Model):
    _name="unprocessed.jplus2"

    _order="date desc"

    date = fields.Datetime(string="Date traitement fichier")
    filename = fields.Char(string="Nom du fichier")
    line_content = fields.Char(string="Contenu de la ligne")

class account_move_line(models.Model):
    _inherit = "account.move.line"

    reference_delivery=fields.Char(size=256,string="Réference de la remise")

    @api.model
    def _unreconcile_invalid_cheque(self):
        """
        Cette fonction traite les lignes des chéques du fichier j+2  remis à Portnet par la BCME .Les lignes  contiennent : la référence du régelement , la ref de
        remise , le montant et le statu (payé ou impayé).
        Si impaye on met à jour le champ ref remise du paiement et de ces écritures comptable et on annulle le letterage.
        Si payé on met à jour le champ ref remise du paiement et de ces écritures comptable.
        :return:
        """
        dirpath=self.env["folder.path.setting"].get_cheque_folder(True)
        if dirpath :
            bank_ids=self.env["res.bank"].search([('check_unpaid','=',True),('bic','!=',False)])
            for bank in bank_ids :
                journal_id=self.env["account.journal"].search([('bank_id',"=",bank.id),('type','=','bank')])
                bank_folder= os.path.join(dirpath, bank.bic)
                if os.path.exists(bank_folder):
                    loaded_path=os.path.join(bank_folder, 'loaded')
                    rejected_path=os.path.join(bank_folder, 'rejected')
                    if not os.path.exists(rejected_path):
                        os.makedirs(rejected_path)
                        os.chmod(rejected_path,0777)
                    if not os.path.exists(loaded_path):
                        os.makedirs(loaded_path)
                        os.chmod(loaded_path,0777)
                    for filename in glob.glob(os.path.join(bank_folder, '*.csv')):
                          filepath=os.path.join(dirpath, filename)
                          csvfile=open(filepath)
                          #dialect = csv.Sniffer().sniff(csvfile.read(1024))
                          csvfile.seek(0)
                          reader = csv.reader(csvfile, delimiter=';', quotechar='|')
                          nbr_line_processed=0
                          unprocessed_lines=[]
                          namefile=os.path.basename(filepath)
                          new_filepath=loaded_path+'/'+namefile
                          out=open(new_filepath, 'wb')
                          reject_path=os.path.join(rejected_path,os.path.splitext(namefile)[0]+"_rejets_.csv")
                          out_reject=open(reject_path, 'wb')
                          writer = csv.writer(out)
                          reject_writer=csv.writer(out_reject)
                          for line in reader:
                              if len(line)==0:
                                  nbr_line_processed+=1
                                  continue

                              if line[3]=='unpaid' :
                                    move_ids=self.env["account.move"].search([('ref',"=",line[0]),('journal_id','=',journal_id.id),
                                                                ('amount','=',line[2])])
                                    if move_ids:
                                        for move_id in move_ids:
                                            voucher_id=self.env["account.voucher"].search([('move_id','=',move_id.id),('reference_delivery','=',False)])
                                            if voucher_id :
                                                voucher_id.write({'reference_delivery':line[1]})
                                                nbr_line_processed+=1
                                                for move_line in move_id.line_id :
                                                    move_line.write({'reference_delivery':line[1]})
                                                voucher_id.cancel_voucher()
                                                writer.writerow(line)
                                            else :
                                                motif = "NoPaymentFound"
                                                line.append(motif)
                                                unprocessed_lines.append(line)
                                                reject_writer.writerow(line)
                                    else :
                                        motif = "NoAccountMoveLineFound OR AmountError"
                                        line.append(motif)
                                        unprocessed_lines.append(line)
                                        reject_writer.writerow(line)

                              if line[3]=='paid' :
                                  move_ids=self.env["account.move"].search([('ref',"=",line[0]),('journal_id','=',journal_id.id),
                                                                ('amount','=',line[2])])
                                  if move_ids :
                                      for move_id in move_ids :
                                          voucher_id=self.env["account.voucher"].search([('move_id','=',move_id.id),('reference_delivery','=',False)])
                                          if voucher_id :
                                              voucher_id.write({'reference_delivery':line[1]})
                                              nbr_line_processed+=1
                                              writer.writerow(line)
                                          else :
                                               motif = "NoPaymentFound"
                                               line.append(motif)
                                               unprocessed_lines.append(line)
                                               reject_writer.writerow(line)
                                          for move_line in move_id.line_id :
                                              if not move_line.reference_delivery :
                                                  move_line.write({'reference_delivery':line[1]})
                                              else :
                                                    motif = "ReferenceDeliveryAlreadyExist"
                                                    line.append(motif)
                                                    unprocessed_lines.append(line)
                                                    reject_writer.writerow(line)
                                  else :
                                       motif = "NoAccountMoveLineFound OR AmountError"
                                       line.append(motif)
                                       unprocessed_lines.append(line)
                                       reject_writer.writerow(line)
                          unprocessed_obj=self.env["unprocessed.jplus2"]
                          for line in unprocessed_lines :
                              date_now = time.strftime("%Y-%m-%d %H:%M:%S")
                              vals= {
                                  "date":date_now,
                                  "filename":namefile,
                                  "line_content":line,
                                     }
                              unprocessed_obj.create(vals)
                          os.remove(filename)
                          if os.stat(reject_path).st_size == 0:
                              os.remove(reject_path)


                else :
                     code='exchange_folder_error'
                     output="Il n'existe pas un dossier des échanges pour la banque %s dans le serveur"%(bank.name)
                     type="exchange"
                     self.env['report.exception'].set_exception(code,output)

        return True




account_move_line()
