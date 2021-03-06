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


from openerp import models, fields, api, _, exceptions
from openerp.osv import osv
from openerp.tools import float_compare
from xml.dom import minidom
from datetime import datetime
import time
import os, os.path ,glob
from dateutil import parser, rrule
import itertools
import logging


class account_invoice(models.Model):

      _inherit="account.invoice"


      @api.v8
      def pay_and_reconcile(self, pay_amount, pay_account_id, period_id, pay_journal_id,
                          writeoff_acc_id, writeoff_period_id, writeoff_journal_id, name=''):
        print "V8 ---pay_and_reconcile"
        # TODO check if we can use different period for payment and the writeoff line
        assert len(self)==1, "Can only pay one invoice at a time."
        # Take the seq as name for move
        SIGN = {'out_invoice': -1, 'in_invoice': 1, 'out_refund': 1, 'in_refund': -1}
        direction = SIGN[self.type]
        # take the chosen date
        date = self._context.get('date_p') or fields.Date.context_today(self)

        # Take the amount in currency and the currency of the payment
        if self._context.get('amount_currency') and self._context.get('currency_id'):
            amount_currency = self._context['amount_currency']
            currency_id = self._context['currency_id']
        else:
            amount_currency = False
            currency_id = False

        pay_journal = self.env['account.journal'].browse(pay_journal_id)
        if self.type in ('in_invoice', 'in_refund'):
            ref = self.reference
        else:
            ref = self.number
        partner = self.partner_id._find_accounting_partner(self.partner_id)
        name = name or self.invoice_line[0].name or self.number
        # Pay attention to the sign for both debit/credit AND amount_currency
        l1 = {
            'name': name,
            'debit': direction * pay_amount > 0 and direction * pay_amount,
            'credit': direction * pay_amount < 0 and -direction * pay_amount,
            'account_id': self.account_id.id,
            'partner_id': partner.id,
            'ref': ref,
            'date': date,
            'currency_id': currency_id,
            'amount_currency': direction * (amount_currency or 0.0),
            'company_id': self.company_id.id,
        }
        l2 = {
            'name': name,
            'debit': direction * pay_amount < 0 and -direction * pay_amount,
            'credit': direction * pay_amount > 0 and direction * pay_amount,
            'account_id': pay_account_id,
            'partner_id': partner.id,
            'ref': ref,
            'date': date,
            'currency_id': currency_id,
            'amount_currency': -direction * (amount_currency or 0.0),
            'company_id': self.company_id.id,
        }
        move = self.env['account.move'].create({
            'ref': ref,
            'line_id': [(0, 0, l1), (0, 0, l2)],
            'journal_id': pay_journal_id,
            'period_id': period_id,
            'date': date,
        })

        move_ids = (move | self.move_id).ids
        self._cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s",
                         (tuple(move_ids),))
        lines = self.env['account.move.line'].browse([r[0] for r in self._cr.fetchall()])
        lines2rec = lines.browse()
        total = 0.0
        for line in itertools.chain(lines, self.payment_ids):
            if line.account_id == self.account_id:
                lines2rec += line
                total += (line.debit or 0.0) - (line.credit or 0.0)

        inv_id, name = self.name_get()[0]
        if not round(total, self.env['decimal.precision'].precision_get('Account')) or writeoff_acc_id:
            print "lines2reclines2rec",lines2rec.ids,writeoff_acc_id,writeoff_period_id,writeoff_journal_id
            try:
                self.pool.get('account.move.line').reconcile(self._cr,self._uid,lines2rec.ids,'manual', writeoff_acc_id, writeoff_period_id, writeoff_journal_id,context=None)
            except Exception as e:
                print e
                logging.error(e)

        else:
            code = self.currency_id.symbol
            # TODO: use currency's formatting function
            msg = _("Invoice partially paid: %s%s of %s%s (%s%s remaining).") % \
                    (pay_amount, code, self.amount_total, code, total, code)
            self.message_post(body=msg)
            lines2rec.reconcile_partial('manual')

        # Update the stored value (fields.function), so we write to trigger recompute
        return self.write({})


      def _create_an_invoice_payment(self,invoice_id,payment_date,amount,journal_id,account_id):
          period_id = self.env['account.period'].find(payment_date)
          period_id = self.env['account.period'].find(payment_date).id
          name="Paiement electronique facture :"+str(self.number)
          amount=round(amount,2)
          print "----------amount--#--------",amount,account_id
          invoice_id.pay_and_reconcile(amount,account_id.id,period_id,journal_id.id,account_id.id,period_id,journal_id.id,name)

class account_voucher(models.Model):
      _inherit='account.voucher'
      _description="les paiement de clients"

      reference_delivery=fields.Char(size=256,string='R??f??rence de la remise')
      traite=fields.Boolean('Trait?? ?', default=False)
      numero_message=fields.Char('Num??ro de message')


      @api.multi
      def _check_amounts_ok(self,type):
          total_amount = 0.00
          if type == 'receipt':
            for line in self.line_cr_ids:
                total_amount += line.amount
          elif type == 'payment':
            for line in self.line_dr_ids:
                total_amount += line.amount

          if self.amount != total_amount and self.reglement_method_id.name == 'Ch??que':
              return False
          else:
              return True

      def proforma_voucher(self, cr, uid, ids, context=None):
          print "in proforma_voucher"
          print "context = ",context
          voucher_record = self.pool.get('account.voucher').browse(cr, uid, ids[0])
          print "type =",voucher_record.type
          res = voucher_record._check_amounts_ok(voucher_record.type)
          #if not res :
          #  raise exceptions.ValidationError("Le montant du paiement est sup??rieur au total des allocations !")
          self.action_move_line_create(cr, uid, ids, context=context)
          return True


      @api.model
      def _payments_deposit(self):

        dirpath=self.env["folder.path.setting"].get_odoo_payments_folder()
        if not dirpath:
            raise exceptions.ValidationError("Erreur d'acc??s au r??p??rtoire de d??p??t des paiements, veuillez contacter votre administrateur")
        os.chdir(dirpath)
        payments = self.env['account.voucher'].search([('traite','=',False),('reglement_method_id','=',2),('reference_delivery','!=',False),('type','in',['sale','receipt']),('state','=','posted')])
        # payments=[]
        # for pay in payment_ids:
        #     if pay.reglement_method_id.name=='Ch??que':
        #         payments.append(pay)

        for p in payments:
            p.numero_message = self.env['ir.sequence'].next_by_code('xml.voucher.seq')
            xml_payment= p._gen_xml_file()[0]
            f =  open(str(fields.date.today())+"-"+str(p.id)+".xml", "ab+")
            print xml_payment
            f.write(xml_payment)
            f.close()
            p.traite=True

      @api.one
      def _gen_xml_file(self):
          #cr??ation document
          newdoc = minidom.Document()
          #cr??ation racine xml
          newroot = newdoc.createElement('pn:NotificationPaiement')
          rootattr = newdoc.createAttribute('xmlns')
          #attribution de la racine au document
          newdoc.appendChild(newroot)
          #Cr??ation et Ajout des autres ??l??ments ?? l'arbre XML
              ## PaiementsMessage
          PaiementsMessage = newdoc.createElement('NotificationPaiementMessage')
          newroot.appendChild(PaiementsMessage)
                  ### HeaderMessage
          HeaderMessage = newdoc.createElement('Entete')
          PaiementsMessage.appendChild(HeaderMessage)
                      #### NumeroMessage
          NumeroMessage=newdoc.createElement('NumeroMessage')
          print self.numero_message
          text = newdoc.createTextNode(self.numero_message)
          NumeroMessage.appendChild(text)
          HeaderMessage.appendChild(NumeroMessage)
                      #### Emetteur
          Emetteur = newdoc.createElement('Emetteur')
          text = newdoc.createTextNode('ODOO')
          Emetteur.appendChild(text)
          HeaderMessage.appendChild(Emetteur)
                      #### Destinataire
          Destinataire = newdoc.createElement('Destinataire')
          text = newdoc.createTextNode('PORTNET')
          Destinataire.appendChild(text)
          HeaderMessage.appendChild(Destinataire)
                      #### DateMessage
          DateMessage = newdoc.createElement('DateMessage')
          text = newdoc.createTextNode(str(datetime.now()))
          DateMessage.appendChild(text)
          HeaderMessage.appendChild(DateMessage)
                      #### TypeMessage
          TypeMessage = newdoc.createElement('TypeMessage')
          text = newdoc.createTextNode('PNM')
          TypeMessage.appendChild(text)
          HeaderMessage.appendChild(TypeMessage)
                      #### fonction
          Fonction = newdoc.createElement('Fonction')
          text = newdoc.createTextNode('1')
          Fonction.appendChild(text)
          HeaderMessage.appendChild(Fonction)
                  ### DonneesPaiement
          DonneesPaiement = newdoc.createElement('DonneesPaiement')
          PaiementsMessage.appendChild(DonneesPaiement)
                    #### Moyen
          Moyen = newdoc.createElement('Moyen')
          text = newdoc.createTextNode('1')
          Moyen.appendChild(text)
          DonneesPaiement.appendChild(Moyen)
                                #### IdTransaction
          IdTransaction = newdoc.createElement('IdTransaction')
          text = newdoc.createTextNode(self.reference)
          IdTransaction.appendChild(text)
          DonneesPaiement.appendChild(IdTransaction)
                     ##### DatePaiement
          DatePaiement = newdoc.createElement('DatePaiement')
          text = newdoc.createTextNode(str(self.date))
          DatePaiement.appendChild(text)
          DonneesPaiement.appendChild(DatePaiement)
                    ##### MontantTotal
          MontantTotal = newdoc.createElement('MontantTotal')
          text = newdoc.createTextNode(str(self.amount))
          MontantTotal.appendChild(text)
          DonneesPaiement.appendChild(MontantTotal)
                    ##### Factures
          Factures = newdoc.createElement('Factures')
          DonneesPaiement.appendChild(Factures)
                              ###### Facture
          for line in self.line_cr_ids:
              if line.reconcile:
                  Facture = newdoc.createElement('Facture')
                  Factures.appendChild(Facture)
                                      ####### NumeroFacture
                  Reference = newdoc.createElement('NumeroFacture')
                  text = newdoc.createTextNode(line.move_line_id and str(line.move_line_id.ref) or str(False))
                  Reference.appendChild(text)
                  Facture.appendChild(Reference)
                                      ####### datefacture
                  DateFacture = newdoc.createElement('DateFacture')
                  text = newdoc.createTextNode(str(line.move_line_id.date ) or str(False))
                  DateFacture.appendChild(text)
                  Facture.appendChild(DateFacture)
                            ##### DateReglement
                  DateReglement = newdoc.createElement('DateReglement')
                  text = newdoc.createTextNode(str(self.date))
                  DateReglement.appendChild(text)
                  Facture.appendChild(DateReglement)
                                      ##### Devise
                  Devise = newdoc.createElement('Devise')
                  text = newdoc.createTextNode(str(self.currency_id.name))
                  Devise.appendChild(text)
                  Facture.appendChild(Devise)
                                      ##### MontantTTC
                  MontantTTC = newdoc.createElement('MontantTTC')
                  text = newdoc.createTextNode(str(line.amount_original) or str(0))
                  MontantTTC.appendChild(text)
                  Facture.appendChild(MontantTTC)

                    ##### Operateur
          Operateur = newdoc.createElement('Operateur')
          PaiementsMessage.appendChild(Operateur)
                    ###### Nom
          Nom = newdoc.createElement('Nom')
          text = newdoc.createTextNode(str(self.partner_id.name))
          Nom.appendChild(text)
          Operateur.appendChild(Nom)
                    ###### IdentifiantDouane
          IdentifiantDouane = newdoc.createElement('IdentifiantDouane')
          text = newdoc.createTextNode(str(self.partner_id.code))
          IdentifiantDouane.appendChild(text)
          Operateur.appendChild(IdentifiantDouane)
                    ###### Adresse
          Adresse = newdoc.createElement('Adresse')
          text = newdoc.createTextNode(str(self.partner_id.city))
          Adresse.appendChild(text)
          Operateur.appendChild(Adresse)
                    ###### TypeIdentification
          TypeIdentification = newdoc.createElement('TypeIdentification')
          text = newdoc.createTextNode('IFU')
          TypeIdentification.appendChild(text)
          Operateur.appendChild(TypeIdentification)
                            ###### NumIdentification
          NumIdentification = newdoc.createElement('NumIdentification')
          Operateur.appendChild(NumIdentification)
                            ###### Centre
          Centre = newdoc.createElement('Centre')
          Operateur.appendChild(Centre)
                              ###### IFU
          IFU = newdoc.createElement('IdFiscalUnique')
          text = newdoc.createTextNode(str(self.partner_id.ifu))
          IFU.appendChild(text)
          Operateur.appendChild(IFU)
                    ##### Partenaire
          Partenaire = newdoc.createElement('Partenaire')
          PaiementsMessage.appendChild(Partenaire)
                    ###### IdenifiantPartenaire
          IdenifiantPartenaire = newdoc.createElement('IdenifiantPartenaire')
          text = newdoc.createTextNode('611ODOO116')
          IdenifiantPartenaire.appendChild(text)
          Partenaire.appendChild(IdenifiantPartenaire)
                    ###### Localite
          Localite = newdoc.createElement('Localite')
          text = newdoc.createTextNode('NONE')
          Localite.appendChild(text)
          Partenaire.appendChild(Localite)



          #                 ##### Factures
          # Factures = newdoc.createElement('Factures')
          # MessageInfo.appendChild(Factures)
          #                     ###### Facture
          # for line in self.line_cr_ids:
          #     if line.reconcile:
          #         Facture = newdoc.createElement('Facture')
          #         Factures.appendChild(Facture)
          #                             ####### R??f??rence
          #         Reference = newdoc.createElement('Reference')
          #         text = newdoc.createTextNode(line.move_line_id and str(line.move_line_id.ref) or str(False))
          #         Reference.appendChild(text)
          #         Facture.appendChild(Reference)
          #                             ####### Montant de la facture
          #         Montant = newdoc.createElement('Montant')
          #         text = newdoc.createTextNode(str(line.amount_original) or str(0))
          #         Montant.appendChild(text)
          #         Facture.appendChild(Montant)


          return newdoc.toprettyxml(encoding="UTF-8")


      @api.model
      def _parse_xml_payments(self):
        dirpath=self.env["folder.path.setting"].get_portnet_payments_folder()
        if not dirpath:
            raise exceptions.ValidationError("Erreur d'acc??s au r??p??rtoire de lecture des paiements, veuillez contacter votre administrateur")
        os.chdir(dirpath)
        # For each file within that folder:
        for filename in glob.glob(os.path.join(dirpath, '*.XML')):
            filepath=os.path.join(dirpath, filename)
            print filepath
            #Read xml file
            file=open(filepath)
            dom = minidom.parse(file)
            print dom
            obj_xml_history=self.env["xml.history"]
            type_message=dom.getElementsByTagName("TypeMessage")[0].firstChild.nodeValue
            destinataire_message=dom.getElementsByTagName("Destinataire")[0].firstChild.nodeValue
            emetteur_message=dom.getElementsByTagName("Emetteur")[0].firstChild.nodeValue
            if emetteur_message=="PORTNET" and destinataire_message=="611ODOO116" :
                if type_message=="ACC":
                    #Integration des accus??s de r??ception des factures xml envoy?? par Portnet
                    messageref=dom.getElementsByTagName("Reference")[0].firstChild.nodeValue
                    xml_history_id=obj_xml_history.search([('messageref','=',messageref)])
                    if xml_history_id :
                        datemessage=dom.getElementsByTagName("DateMessage")[0].firstChild.nodeValue
                        xml_history_id.acc_date = datemessage
                        note_message=dom.getElementsByTagName("Description")[0].firstChild.nodeValue
                        xml_history_id.note = note_message
                        state_message=dom.getElementsByTagName("Etat")[0].firstChild.nodeValue
                        if state_message == '1':
                            xml_history_id.type='inv_integration_ok'
                        if state_message=='0':
                            xml_history_id.type='inv_integration_nok'
                        print "mise ?? jour xml historique"
                if type_message in ('PNM','INV') :
                    #Get Fonction attribute ( 1 : confirmation and 3 : Annulation)
                    fonction= dom.getElementsByTagName("Fonction")[0].firstChild.nodeValue
                    #Get Payment DATA transaction_id,partner_ref,invoice_number,ident_douane ,ident_partner,localite
                    #Get Payment DATA :Get Transaction
                    try :
                        transaction_id= dom.getElementsByTagName("IdTransaction")[0].firstChild.nodeValue
                    except:
                        transaction_id=""
                    try :
                        ident_douane =  dom.getElementsByTagName("IdentifiantDouane")[0].firstChild.nodeValue
                    except:
                        ident_douane=""
                    ident_partner = dom.getElementsByTagName("IdentifiantPartenaire")[0].firstChild.nodeValue
                    try:
                       localite=dom.getElementsByTagName("Localite")[0].firstChild.nodeValue
                    except:
                        localite="NONE"
                    invoice_number = dom.getElementsByTagName("NumeroFacture")
                    try:
                        partner_ref= dom.getElementsByTagName("NumeroMessage")[0].firstChild.nodeValue
                    except:
                        motif="Num??ro de message de paiement introuvalbe"
                        self._gen_xml_retour_file("0",transaction_id,partner_ref,False,ident_douane,ident_partner,localite,motif)
                    if not invoice_number:
                        # pas encore finalis?? , tous les cas faillure ou scucess doivet retourner un fihcier xml pas encore communiqu?? par PORTNET
                        motif="Num??ro de facture introuvable sur le fichier XML"
                        self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                    elif invoice_number:
                         invoice_number = dom.getElementsByTagName("NumeroFacture")[0].firstChild.nodeValue
                         invoice_id = self.env['account.invoice'].search([('number','=',invoice_number)])
                         if not invoice_id:
                             motif="Facture introuvable dans le syst??me"
                             print motif
                             self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                         elif invoice_id and invoice_id.state == 'paid' and fonction=="1":
                               motif="La facture est d??ja regl??e dans le syst??me"
                               self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                         elif invoice_id and invoice_id.state == 'cancelled' and fonction=="3":
                               motif="La facture est d??ja annul??e dans le syst??me"
                               self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)

                    if fonction=="1" and invoice_id.state != 'paid':
                        #Get payment date
                        payment_date = dom.getElementsByTagName("DatePaiement")
                        if not payment_date:
                            motif="Date de paiement introuvable"
                            self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                        else:
                            string_date  = (payment_date[0].firstChild.nodeValue)[:10]
                            try:
                                payment_date = parser.parse(string_date)
                            except:
                                motif="Date de paiement : format incorrect"
                                self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                        #Get payment amount
                        paid_amount = dom.getElementsByTagName("MontantTTC")
                        if not paid_amount:
                            motif="Montant du paiement introuvable sur le fichier XML"
                            self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                        else:
                            try:
                                amount = float(paid_amount[0].firstChild.nodeValue)
                                if amount<=0 or amount != invoice_id.amount_total:
                                     motif="Montant du paiement ne peut etre different du montant facture"
                                     self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                                     return False
                            except:
                                 motif="Montant du paiement : Format incorrect"
                                 self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                        amount = round(float(paid_amount[0].firstChild.nodeValue),2)
                        journal_pool = self.env['account.journal']
                        journal_type = 'bank'
                        company_id =self.env['res.company']._company_default_get('account.bank.statement')
                        ids = journal_pool.search([('type', '=', journal_type),('company_id','=',company_id)])
                        if not ids:
                            motif="Jouranl de banque introuvable sur le systeme"
                            self._gen_xml_retour_file("0",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)
                        journal_id=ids[0]
                        account_id=journal_id.default_debit_account_id
                        self.env['account.invoice']._create_an_invoice_payment(invoice_id,payment_date,amount,journal_id,account_id)
                        motif="Paiement Facture integree avec succes"
                        print "OK",motif
                        self._gen_xml_retour_file("1",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)

                    if fonction=="3" :
                          print "invoice",invoice_id
                          invoice_id.action_cancel()
                          motif="Facture annulee avec succes"
                          self._gen_xml_retour_file("1",transaction_id,partner_ref,invoice_number,ident_douane,ident_partner,localite,motif)

            # move document to loaded folder
            loaded_path=os.path.join(dirpath, 'loaded')
            filepath=os.path.join(dirpath, filename)
            name=os.path.basename(filepath)
            new_filepath=loaded_path+'/'+name
            os.rename(filepath, new_filepath)
            #self.env.cr.commit()


      def _gen_xml_retour_file(self,status,transaction_id,partner_ref,invoice_number
                               ,ident_douane,ident_partner,localite,comment):
        dirpath=self.env["folder.path.setting"].get_odoo_payments_folder()
        if not dirpath:
            raise exceptions.ValidationError("Erreur d'acc??s au r??pertoire de d??p??t des retours de paiements, veuillez contacter votre administrateur")
        os.chdir(dirpath)
        obj_xml_history=self.env["xml.history"]
        # document creation
        newdoc = minidom.Document()
        # racine xml creation
        newroot1 = newdoc.createElement('pn:NotificationRetour')
        newroot1.setAttribute("xmlns:pn", "http://portnet.ma/NotificationRetour")
        newroot = newdoc.createElement('NotificationRetourMessage')
        newroot1.appendChild(newroot)
        newdoc.appendChild(newroot1)
        # header creation
        header = newdoc.createElement('Entete')
        newroot.appendChild(header)
        # Num??ro d'interchange
        exchange_seq = newdoc.createElement("NumeroMessage")
        text = newdoc.createTextNode(self.env['ir.sequence'].get('xml.exchange.seq'))
        exchange_seq.appendChild(text)
        header.appendChild(exchange_seq)
                ### Emetteur
        Emetteur = newdoc.createElement('Emetteur')
        text = newdoc.createTextNode('611ODOO116')
        Emetteur.appendChild(text)
        header.appendChild(Emetteur)
                ### Destinataire
        Destinataire = newdoc.createElement('Destinataire')
        text = newdoc.createTextNode('611PNET00100')
        Destinataire.appendChild(text)
        header.appendChild(Destinataire)
                ### DateMessage
        DateMessage = newdoc.createElement('DateMessage')
        text = newdoc.createTextNode(str(time.strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
        DateMessage.appendChild(text)
        header.appendChild(DateMessage)
                ### TypeMessage
        TypeMessage = newdoc.createElement('TypeMessage')
        text = newdoc.createTextNode('UNM')
        TypeMessage.appendChild(text)
        header.appendChild(TypeMessage)
                   ### FonctionMessage
        FonctionMessage = newdoc.createElement('Fonction')
        text = newdoc.createTextNode('R')
        FonctionMessage.appendChild(text)
        header.appendChild(FonctionMessage)
            ##cr??ation balise Integration
        integration = newdoc.createElement('Integration')
        newroot.appendChild(integration)
                ### EtatMessage
        state = newdoc.createElement('Etat')
        text = newdoc.createTextNode(status)
        state.appendChild(text)
        integration.appendChild(state)
                ### DateTraitement
        date_process = newdoc.createElement('DateTraitement')
        text = newdoc.createTextNode(str(time.strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
        date_process.appendChild(text)
        integration.appendChild(date_process)
                ### MotifReject
        motif = newdoc.createElement("MotifReject")
        text = newdoc.createTextNode(comment)
        motif.appendChild(text)
        integration.appendChild(motif)
                ### DonneesPaiement
        paymentdata = newdoc.createElement("DonneesPaiement")
        newroot.appendChild(paymentdata)
                ### IdTransaction
        transid = newdoc.createElement("IdTransaction")
        text = newdoc.createTextNode(transaction_id)
        transid.appendChild(text)
        paymentdata.appendChild(transid)
                ### ReferencePartenaire
        refpartner = newdoc.createElement("ReferencePartenaire")
        text = newdoc.createTextNode(partner_ref)
        refpartner.appendChild(text)
        paymentdata.appendChild(refpartner)
            ##cr??ation balise NumeroFacture
        invoice_nbr = newdoc.createElement("NumeroFacture")
        text = newdoc.createTextNode(invoice_number)
        invoice_nbr.appendChild(text)
        paymentdata.appendChild(invoice_nbr)
         ##cr??ation balise IdentifiantDouane
        codedoaune = newdoc.createElement("IdentifiantDouane")
        text = newdoc.createTextNode(ident_douane)
        codedoaune.appendChild(text)
        paymentdata.appendChild(codedoaune)
        # IdentifiantPartenaire node creation
        partner_ident = newdoc.createElement("IdentifiantPartenaire")
        text = newdoc.createTextNode(ident_partner)
        partner_ident.appendChild(text)
        paymentdata.appendChild(partner_ident)
        # Locality node creation
        partner_loc = newdoc.createElement("Localite")
        text = newdoc.createTextNode(localite)
        partner_loc.appendChild(text)
        paymentdata.appendChild(partner_loc)
        # FILE DEPOSIT
        xml_payment_integration = newdoc.toprettyxml(encoding="UTF-8")
        date_now_str = str(time.strftime("%Y-%m-%d %H:%M:%S"))
        date_now_str = date_now_str.replace('-', '')
        date_now_str = date_now_str.replace(':', '')
        date_now_str = date_now_str.replace(' ', 'T')
        code_edi_odoo = "9999"
        message_type = 'UNM'
        filename_txt = code_edi_odoo+message_type+date_now_str+self.env['ir.sequence'].get('xml.filename.seq')
        text = newdoc.createTextNode(filename_txt)
        f = open(filename_txt+".xml", "ab+")
        f.write(xml_payment_integration)
        f.close()
        # payment xml history
        xml_history_ids = obj_xml_history.search([('invoice_number','=', invoice_number)])
        print "invoice_numberinvoice_number",invoice_number,xml_history_ids
        if xml_history_ids:
            for xml_history_id in xml_history_ids :
                #todo : tester si 'il y aplusieurs lignes avec le meme num??ro , ajouter un autre attriber
                xml_history_id.first_payment_load_date = date_now_str
                xml_history_id.note = comment
                xml_history_id.transaction_id = transaction_id
                if status == "1":
                    xml_history_id.type = 'payment_integration_ok'
                else:
                    xml_history_id.type = 'payment_integration_nok'
        return True


      def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        if voucher.type in ('purchase', 'payment'):
            credit = voucher.paid_amount_in_company_currency
        elif voucher.type in ('sale', 'receipt'):
            debit = voucher.paid_amount_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        move_line = {
                'name': voucher.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': voucher.account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': (sign * abs(voucher.amount) # amount < 0 for refunds
                    if company_currency != current_currency else 0.0),
                'date': voucher.date,
                'date_maturity': voucher.date_due
            }
        if voucher.reference_delivery:
           move_line['reference_delivery']= voucher.reference_delivery
        return move_line

      def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        '''
        Set a dict to be use to create the writeoff move line.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        currency_obj = self.pool.get('res.currency')
        move_line = {}

        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id

        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
            diff = line_total
            account_id = False
            write_off_name = ''
            if voucher.payment_option == 'with_writeoff':
                account_id = voucher.writeoff_acc_id
                write_off_name = voucher.comment
            elif voucher.partner_id:
                if voucher.type in ('sale', 'receipt'):
                    account_id = voucher.partner_id.property_account_receivable
                else:
                    account_id = voucher.partner_id.property_account_payable
            else:
                # fallback on account of voucher
                account_id = voucher.account_id
            sign = voucher.type == 'payment' and -1 or 1
            move_line = {
                'name': write_off_name or name,
                'account_id': account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'date': voucher.date,
                'credit': diff > 0 and diff or 0.0,
                'debit': diff < 0 and -diff or 0.0,
                'amount_currency': company_currency <> current_currency and (sign * -1 * voucher.writeoff_amount) or 0.0,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
            }

            # code kzc
            if voucher.reference_delivery:
               move_line['reference_delivery']= voucher.reference_delivery

        return move_line

      def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []

        date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = line.type =='dr' and -1 or 1
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date
            }
            if voucher.reference_delivery:
               move_line['reference_delivery']= voucher.reference_delivery
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': (-1 if line.type == 'cr' else 1) * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                }
                if voucher.reference_delivery:
                   move_line['reference_delivery']= voucher.reference_delivery
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        return (tot_line, rec_lst_ids)

account_voucher()

