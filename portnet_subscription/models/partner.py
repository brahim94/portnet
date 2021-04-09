# -*- encoding: utf-8 -*-

from openerp.osv import osv
from openerp import SUPERUSER_ID,models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp
import datetime

from string import Template
import requests
import time
import concurrent.futures
import xml.etree.ElementTree as ET


messagetemplateactivation=Template(r"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sous="http://souscription.ws.portnet.portel.es/">
   <soapenv:Header/>
   <soapenv:Body>
      <sous:desaCompany>
         <!--Optional:-->
         <login>$login</login>
         <!--Optional:-->
         <password>$pwd</password>
         <!--Optional:-->
         <hmac>$hmac</hmac>
         <!--Optional:-->
         <category>$categorie</category>
         <!--Optional:-->
         <idCompany>$id_portnet</idCompany>
         <!--Optional:-->
         <deactivate>$desactivation</deactivate>
      </sous:desaCompany>
   </soapenv:Body>
</soapenv:Envelope>
""")


messagetemplateimport=Template(r"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sous="http://souscription.ws.portnet.portel.es/">
   <soapenv:Header/>
   <soapenv:Body>
      <sous:addCompanyImpExp>
         <!--Optional:-->
         <login>$login</login>
         <!--Optional:-->
         <password>$pwd</password>
         <!--Optional:-->
         <hmac>$hmac</hmac>
         <code>$code</code>
         <!--Optional:-->
         <centreRC>$centrerc</centreRC>
         <!--Optional:-->
         <numeroRC>$numerorc</numeroRC>
         <!--Optional:-->
         <ifu>$ifu</ifu>
         <!--Optional:-->
         <agrement>$agrement</agrement>
         <!--Optional:-->
         <description>$description</description>
         <!--Optional:-->
         <ice>$ice</ice>
         <!--Optional:-->
         <siegeSocial>$siegesocial</siegeSocial>
         <!--Optional:-->
         <taxeProfessionnelle>$taxepro</taxeProfessionnelle>
         <!--Optional:-->
         <numFichierDCE>$numdce</numFichierDCE>
         <idImpExp>$imp_exp</idImpExp>
      </sous:addCompanyImpExp>
   </soapenv:Body>
</soapenv:Envelope>
""")

messagetemplatetransitaire=Template(r"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sous="http://souscription.ws.portnet.portel.es/">
   <soapenv:Header/>
   <soapenv:Body>
      <sous:addCompanyTransitaire>
         <!--Optional:-->
         <login>$login</login>
         <!--Optional:-->
         <password>$pwd</password>
         <!--Optional:-->
         <hmac>$hmac</hmac>
         <code>$code</code>
         <!--Optional:-->
         <centreRC>$centrerc</centreRC>
         <!--Optional:-->
         <numeroRC>$numerorc</numeroRC>
         <!--Optional:-->
         <ifu>$ifu</ifu>
         <!--Optional:-->
         <agrement>$agrement</agrement>
         <!--Optional:-->
         <description>$description</description>
         <!--Optional:-->
         <ice>$ice</ice>
         <idTransitaire>$transitaire</idTransitaire>
      </sous:addCompanyTransitaire>
   </soapenv:Body>
</soapenv:Envelope>
""")

messagetemplateconsignataire = Template(r"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sous="http://souscription.ws.portnet.portel.es/">
   <soapenv:Header/>
   <soapenv:Body>
      <sous:addCompanyConsignataire>
         <!--Optional:-->
         <login>$login</login>
         <!--Optional:-->
         <password>$pwd</password>
         <!--Optional:-->
         <hmac>$hmac</hmac>
         <codeEDI>$codeedi</codeEDI>
         <!--Optional:-->
         <codeANP>$codeanp</codeANP>
         <!--Optional:-->
         <codeMarsaMaroc>$codemarsa</codeMarsaMaroc>
         <!--Optional:-->
         <description>$description</description>
         <!--Optional:-->
         <transitaire>$transitaire</transitaire>
         <idConsignataire>$consignataire</idConsignataire>
      </sous:addCompanyConsignataire>
   </soapenv:Body>
</soapenv:Envelope>
""")

messagetemplatebanque = Template(r"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sous="http://souscription.ws.portnet.portel.es/">
   <soapenv:Header/>
   <soapenv:Body>
      <sous:addCompanyBanque>
         <!--Optional:-->
         <login>$login</login>
         <!--Optional:-->
         <password>$pwd</password>
         <!--Optional:-->
         <hmac>$hmac</hmac>
         <code>$code</code>
         <!--Optional:-->
         <codeEDI>$edi</codeEDI>
         <!--Optional:-->
         <nomBanque>$name</nomBanque>
         <idBanque>$banque</idBanque>
      </sous:addCompanyBanque>
   </soapenv:Body>
</soapenv:Envelope>
""")


messagetemplateoperator = Template(r"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sous="http://souscription.ws.portnet.portel.es/">
   <soapenv:Header/>
   <soapenv:Body>
      <sous:addCompanyOperateur>
         <!--Optional:-->
         <login>$login</login>
         <!--Optional:-->
         <password>$pwd</password>
         <!--Optional:-->
         <hmac>$hmac</hmac>
         <!--Optional:-->
         <code>$code</code>
         <!--Optional:-->
         <description>$description</description>
         <!--Optional:-->
         <centreRC>$centrerc</centreRC>
         <!--Optional:-->
         <numeroRC>$numerorc</numeroRC>
         <!--Optional:-->
         <ifu>$ifu</ifu>
         <!--Optional:-->
         <cin>$cin</cin>
         <!--Optional:-->
         <port>$port</port>
         <!--Optional:-->
         <numLimiteConteneurJour>$nbconteneur</numLimiteConteneurJour>
         <idOperateur>$operator</idOperateur>
      </sous:addCompanyOperateur>
   </soapenv:Body>
</soapenv:Envelope>
""")

messagetemplateutilisateur = Template(r"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sous="http://souscription.ws.portnet.portel.es/">
   <soapenv:Header/>
   <soapenv:Body>
      <sous:addUser>
         <!--Optional:-->
         <login>$login</login>
         <!--Optional:-->
         <password>$pwd</password>
         <!--Optional:-->
         <hmac>$hmac</hmac>
         <!--Optional:-->
         <nomUtilisateurGU>$name</nomUtilisateurGU>
         <!--Optional:-->
         <prenomUtilisateurGU>$prenom</prenomUtilisateurGU>
         <!--Optional:-->
         <cin>$cin</cin>
         <!--Optional:-->
         <email>$email</email>
         <!--Optional:-->
         <dateExpirationCIN>$expcin</dateExpirationCIN>
         <!--Optional:-->
         <domiciliationCIN>$domiciliationcin</domiciliationCIN>
         <!--Optional:-->
         <payCode>$paycode</payCode>
         <!--Optional:-->
         <telephone>$phone</telephone>
         <!--Optional:-->
         <impCode>$impcode</impCode>
         <!--Optional:-->
         <expCode>$expcode</expCode>
         <!--Optional:-->
         <conCodeANP>$codeanp</conCodeANP>
         <!--Optional:-->
         <tranCode>$codetran</tranCode>
         <!--Optional:-->
         <banqueCode>$banquecode</banqueCode>
         <!--Optional:-->
         <operateurCode>$operateurcode</operateurCode>
      </sous:addUser>
   </soapenv:Body>
</soapenv:Envelope>
""")


headers = {'SOAPAction': 'addCompanyImpExp','Content-Type':'text/xml;charset=UTF-8'}


class res_partner(models.Model):
      _name = 'res.partner'
      _inherit = 'res.partner'

      cnss = fields.Char(string='CNSS',required=False)
      raison_social = fields.Char(string='Raison Sociale',required=False)
      professional_tax = fields.Char(string='Taxe profesionnelle',required=False)
      paiement_mode = fields.Selection([('cash','Espèce'),('CHEQUE','Chèque'),('AMANPAY','AMANPAY'),('VIREMENT','VIREMENT')],string='Moyen de paiement')
      customer_type = fields.Selection([('physical','Personne physique'),('corporation','Personne Morale')],string='Type d\'entité',required=False)
      agrement = fields.Char(string='Agrément' ,size=80)
      first_name = fields.Char(string='Prénom du représentant' ,size=80)
      bank = fields.Char(string='Banque')
      ## Importateur
      categ_code = fields.Char(string='Code',related='categ_id.code')
      file_dce = fields.Char(string='N° Fichier DCE')
      ## Operateur
      code_EDI = fields.Char(string='Code EDI')
      port = fields.Char(string='Port')
      number_containers = fields.Integer(string='Nombre conteneurs par jour')
      cin = fields.Char(string='CIN')
      ##Consignataire
      code_anp = fields.Char(string='Code ANP')
      code_marsa = fields.Char(string='Code Marsa Maroc')
      transitaire = fields.Char(string='Transitaire')
      ##Transitaire
      douanier_ids = fields.One2many('bureau.douanier','partner_id',string='Liste Transitaires')
      ##Web services response
      portnet_id = fields.Integer(string='ID PORTNET')
      response_portnet = fields.Text(string='Reponse PORTNET',readonly=True)
      ##Infos Contact
      cin = fields.Char(string="CIN")
      expiration_cin = fields.Date(string="Date Expiration CIN")
      domiciliation_cin = fields.Char(string="Domiciliation CIN")
      last_name = fields.Char(string='Prénom')
      direction_type = fields.Selection([('administration','Direction Administrative'),
                                         ('logistic','Direction Logistique'),
                                         ('commercial','Direction Commerciale'),
                                         ('operations','Direction des opérations'),
                                         ('ressourceshumaines','Direction des ressources humaines'),
                                         ('achats','Direction des achats'),
                                         ('generale','Direction générale'),
                                         ('presidencegenerale','Présidence direction générale'),
                                         ('systemeinformation','Direction des systèmes d information'),
                                         ('communication','Direction communication'),
                                         ('marketing','Direction marketing'),
                                         ('audit','Direction audit'),
                                         ('controlegestion','Direction contrôle de gestion'),
                                         ('financiere','Direction financière'),
                                         ('transportlogistique','Direction transport et logistique'),
                                         ('recherchedeveloppement','Direction recherche et développement'),
                                         ('autres','Autres')
                                         ],
                                          string='Type direction')
      is_representative = fields.Boolean(string='Mondataire ?')
      ##Guichet unqiue Users
      portnet_user_ids = fields.One2many('user.portnet','partner_id',string='Utilisateurs Guichet Unique')
      gu_operations_history = fields.One2many('compte.gu.operation.history','partner_id',string='Historiques Opérations G.U')
      site_institutionnel_id = fields.Integer(string='ID SITE INSTIUTIONNEL',readonly=True)
      active_gu = fields.Boolean(string="Activ GU ?", default=True)
      extra_partner_id = fields.Integer(string='Extra Partner ID')
      extra_is_paid = fields.Boolean(string='Is paid')
      auto_activation = fields.Boolean(string="Activation Automatique",default=True)


      # Retrieve a single page and report the URL and contents
      def fire_post_request(self, url, data, timeout):
          start_time = time.time()
          response = requests.post(url, data=data, timeout=timeout, headers=headers)
          end_time = time.time() - start_time
          return {'responsetime': end_time, 'response': response}


      @api.multi
      def synchronise_gu(self, max_workers=100):
          res = self.env['setting.guichet.unique'].search([])
          if len(res) == 0:
              raise Warning("Veuillez saisir les paramètres de la synchronisation GU")
          else:
             url = res.url
             login = res.login
             pwd = res.passwd
             hmac = res.hmac
          with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
              future_to_line = {}
              for line in self:
                 if line.categ_id.code == "I" or line.categ_id.code == "EXP":
                    code = line.code or ''
                    centrerc = line.centre_rc or ''
                    numerorc = line.rc or ''
                    agrement = line.agrement or ''
                    ice = line.ice or ''
                    ifu = line.ifu or ''
                    siegesocial = line.raison_social or ''
                    taxepro = line.professional_tax or ''
                    numdce = line.file_dce or ''
                    description = ''
                    if line.name:
                        description = line.name
                    imp_exp = line.portnet_id or ""
                    data = messagetemplateimport.substitute(login=login, pwd=pwd, hmac=hmac, code=code, centrerc=centrerc,
                                                            numerorc=numerorc,
                                                            agrement=agrement, description=description, ifu=ifu, ice=ice,
                                                            siegesocial=siegesocial,
                                                            taxepro=taxepro, numdce=numdce, imp_exp=imp_exp)
                    future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                 if line.categ_id.code == "T":
                    code = line.code or ''
                    centrerc = line.centre_rc or ''
                    numerorc = line.rc or ''
                    ifu = line.ifu or ''
                    agrement = line.agrement or ''
                    ice = line.ice or ''
                    description = ''
                    if line.name:
                        description = line.name
                    transitaire = line.portnet_id or ""
                    data = messagetemplatetransitaire.substitute(login=login, pwd=pwd, hmac=hmac, code=code,
                                                                 centrerc=centrerc, numerorc=numerorc,
                                                                 agrement=agrement, description=description, ifu=ifu,
                                                                 ice=ice, transitaire=transitaire)
                    future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                 if line.categ_id.code == "CONS":
                    edi = ''
                    anp = ''
                    description = ''
                    transitaire = ''
                    consignataire = ''
                    if line.code_EDI:
                        edi = line.code_EDI
                    if line.code_EDI:
                        anp = line.code_anp
                    if line.name:
                        description = line.name
                    if line.transitaire:
                        transitaire = line.transitaire
                    consignataire = line.portnet_id or ""
                    marsa = line.code_marsa or ''
                    data = messagetemplateconsignataire.substitute(login=login, pwd=pwd, hmac=hmac, codeedi=edi,
                                                                   codeanp=anp, codemarsa=marsa,
                                                                   description=description, transitaire=transitaire,
                                                                   consignataire=consignataire)
                    future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                 if line.categ_id.code == "BANQUES":
                    name = line.name or ''
                    code = line.code or ''
                    edi = line.code_EDI or ''
                    banque = line.portnet_id or ""
                    data = messagetemplatebanque.substitute(login=login, pwd=pwd, hmac=hmac, code=code, edi=edi, name=name,
                                                            banque=banque)
                    future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                 if line.categ_id.code == "OPM":
                    name = line.name or ''
                    code = line.code or ''
                    edi = line.code_EDI or ''
                    centrerc = line.centre_rc or ''
                    numerorc = line.rc or ''
                    ice = line.ice or ''
                    ifu = line.ifu or ''
                    cin = line.cin or ''
                    port = line.port or ''
                    containers = line.number_containers or 0
                    description = line.name or ''
                    operator = line.portnet_id or ""
                    data = messagetemplateoperator.substitute(login=login, pwd=pwd, hmac=hmac,
                                                               name=name, code=edi,
                                                              centrerc=centrerc, numerorc=numerorc,
                                                              ice=ice, ifu=ifu, cin=cin, port=port,
                                                              description=description, nbconteneur=containers,
                                                              operator=operator)
                    future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

              for future in concurrent.futures.as_completed(future_to_line):
                 try:
                    data = future.result()['response']
                    root = ET.fromstring(data.content)
                    for info in root.iter('info'):
                        info_list = (info.text).split(":")
                        if len(info_list) > 1:
                            self.portnet_id = int(info_list[1])
                        self.response_portnet = info.text
                 except Exception as exc:
                    raise exceptions.ValidationError(exc)

              for line in self:
                 for child in line.portnet_user_ids:
                    firstname = child.first_name
                    lastname = child.last_name
                    cin = child.cin
                    expiration_cin = child.expiration_cin
                    domiciliation_cin = child.domiciliation_cin
                    codepay = line.country_id.code
                    email = child.email
                    impcode = ''
                    expcode = ''
                    codeanp = ''
                    codetran = ''
                    banqueCode = ''
                    phone = ''
                    operateurCode = ''
                    if line.categ_id.code == "I":
                        impcode = line.code
                    if line.categ_id.code == "EXP":
                        expcode = line.code
                    if line.categ_id.code == "CONS":
                        codeanp = line.code_anp
                    if line.categ_id.code == "T":
                        codetran = line.code
                    if line.categ_id.code == "BANQUES":
                        banqueCode = line.code
                    if line.categ_id.code == "OPM":
                        operateurCode = line.code
                    data = messagetemplateutilisateur.substitute(pwd=pwd, hmac=hmac,
                                                                 login=login, name=firstname, prenom=lastname,
                                                                 cin=cin, expcin=expiration_cin,
                                                                 domiciliationcin=domiciliation_cin,
                                                                 paycode=codepay, email=email, phone=phone, impcode=impcode,
                                                                 expcode=expcode, codeanp=codeanp, codetran=codetran,
                                                                 banquecode=banqueCode, operateurcode=operateurCode)
                    future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = child
                    for future in concurrent.futures.as_completed(future_to_line):
                        try:
                            data = future.result()['response']
                            root = ET.fromstring(data.content)
                            for info in root.iter('info'):
                                info_list = (info.text).split(":")
                                if len(info_list) > 1:
                                    child.portnet_id = int(info_list[1])
                                child.response_portnet = info.text
                        except Exception as exc:
                            raise exceptions.ValidationError(exc)


      @api.multi
      def pay_invoice(self):
            self.ensure_one()
            invoice = self.env['account.invoice'].search([('partner_id', '=', self._ids[0])])
            voucher_id = self.env['account.voucher'].create({
                'partner_id': self._ids[0],
                'amount': invoice.type in ('out_refund', 'in_refund') and -invoice.residual or invoice.residual,
                'account_id': self.property_account_receivable.id,
                'journal_id': self.env['account.journal'].search([('code', '=', 'BNK1')]).id,
                'type': invoice.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment',
                'reference': " ",
                'reglement_method_id': self.env.ref('tva_ma.list0').id if self.paiement_mode == 'cash' else self.env.ref(
                    'tva_ma.list1').id,
            })
            res = voucher_id.recompute_voucher_lines(
                partner_id=self.pool.get('res.partner')._find_accounting_partner(invoice.partner_id).id,
                journal_id=self.env['account.journal'].search([('code', '=', 'BQ')]).id,
                price=invoice.type in ('out_refund', 'in_refund') and -invoice.residual or invoice.residual,
                currency_id=invoice.currency_id.id,
                ttype=invoice.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment',
                date=datetime.datetime.today(),
                context=None)
            vals = res['value']
            print
            voucher_id.write({'line_cr_ids': [(0, 0, line) for line in vals['line_cr_ids']],
                              'line_dr_ids': [(0, 0, line) for line in vals['line_dr_ids']]})
            voucher_id.button_proforma_voucher()
            return invoice and invoice[0]


      @api.model
      def generate_profile(self, vals):
          is_paid = vals.get('extra_is_paid', False)
          extra_partner_id = vals.get('extra_partner_id', -1)
          invoice = False
          if is_paid and extra_partner_id == -1:
             partner_id = self.create(vals)
             partner_id.subscribed = False
             if partner_id.categ_id.code != "EXP":
                sub_wizard_id = self.env['customer.subscription.wizard'].with_context(
                    active_ids=[partner_id and partner_id.id]).create({'partner_id': partner_id and partner_id.id})
                sub_wizard_id.action_subscribe()
                invoice = self.env['account.invoice'].search([('partner_id','=',partner_id[0].id)])
                invoice.is_synchronised_gu = False
                # invoice = partner_id.pay_invoice()
             else:
                partner_id.state = 'confirmed'
             partner_id.synchronise_gu(max_workers=100)

          elif is_paid and extra_partner_id != -1:
             partner_id = self.browse(extra_partner_id)
             partner_id.write(vals)
             if partner_id.state == 'draft':
                partner_id.subscribed = False
                if partner_id.categ_id.code != "EXP":
                   sub_wizard_id = self.env['customer.subscription.wizard'].with_context(
                        active_ids=[partner_id and partner_id.id]).create({'partner_id': partner_id and partner_id.id})
                   sub_wizard_id.action_subscribe()
                   # invoice = self.env['account.invoice'].search([('partner_id','=',partner_id[0].id)])
                   # invoice = partner_id.pay_invoice()
                else:
                   partner_id.state = 'confirmed'
                partner_id.synchronise_gu(max_workers=100)
          else:
             partner_id = self.create(vals)
             partner_id.subscribed = False
             invoice = False

          return {'partner_id': partner_id and partner_id.id,
                'invoice_id': invoice and invoice.number or 0}


      @api.multi
      def activ_gu(self, max_workers=100):
            res = self.env['setting.guichet.unique'].search([])
            if len(res) == 0:
                raise Warning("Veuillez saisir les paramètres de la synchronisation GU")
            else:
                url = res.url
                login = res.login
                pwd = res.passwd
                hmac = res.hmac
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_line = {}
                for line in self:
                    if line.categ_id.code == "I" or line.categ_id.code == "EXP":
                        categorie = 'importExport'
                        if line.portnet_id:
                            portnet_id = line.portnet_id or ''
                        else:
                            raise osv.except_osv(_('Error!'), _(
                                "Ce Client N'est Pas Syncroniser Avec Le Guichet Unique"))
                        desactivation = 'false'
                        data = messagetemplateactivation.substitute(login=login, pwd=pwd, hmac=hmac,
                                                                    categorie=categorie, id_portnet=portnet_id,
                                                                    desactivation=desactivation)
                        future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                    if line.categ_id.code == "T":
                        categorie = 'transitaire'
                        if line.portnet_id:
                            portnet_id = line.portnet_id or ''
                        else:
                            raise osv.except_osv(_('Error!'), _(
                                "Ce Client N'est Pas Syncroniser Avec Le Guichet Unique"))
                        desactivation = 'false'
                        data = messagetemplateactivation.substitute(login=login, pwd=pwd, hmac=hmac,
                                                                    categorie=categorie, id_portnet=portnet_id,
                                                                    desactivation=desactivation)
                        future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                    if line.categ_id.code == "CONS":
                        categorie = 'consignataire'
                        if line.portnet_id:
                            portnet_id = line.portnet_id or ''
                        else:
                            raise osv.except_osv(_('Error!'), _(
                                "Ce Client N'est Pas Syncroniser Avec Le Guichet Unique"))
                        desactivation = 'false'
                        print
                        "Data === I am neer data"
                        data = messagetemplateactivation.substitute(login=login, pwd=pwd, hmac=hmac,
                                                                    categorie=categorie, id_portnet=portnet_id,
                                                                    desactivation=desactivation)
                        print
                        "Data === ", data
                        future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                for future in concurrent.futures.as_completed(future_to_line):
                    try:
                        data = future.result()['response']
                        root = ET.fromstring(data.content)
                        for info in root.iter('info'):
                            info_list = (info.text).split(":")
                            if len(info_list) > 1:
                                self.portnet_id = int(info_list[1])
                            self.response_portnet = info.text
                    except Exception as exc:
                        raise exceptions.ValidationError("Problème de Connexion GU")
                date_format = '%Y-%m-%d'
                today = (datetime.datetime.today()).strftime(date_format)
                d1 = datetime.datetime.strptime(today, date_format)
                now = fields.Datetime.now()
                vals = {
                    'name': "Activation du Profil " + str(self.name),
                    'time':now,
                    'date': d1,
                    'partner_id': self.id,
                    'categ_id': self.categ_id.id,
                    'state': 'activation',
                }
                self.env['compte.gu.operation.history'].create(vals)
                self.active_gu = True


      @api.multi
      def desactiv_gu(self, max_workers=100):
            res = self.env['setting.guichet.unique'].search([])
            if len(res) == 0:
                raise Warning("Veuillez saisir les paramètres de la synchronisation GU")
            else:
                url = res.url
                login = res.login
                pwd = res.passwd
                hmac = res.hmac
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_line = {}
                for line in self:
                    if line.categ_id.code == "I" or line.categ_id.code == "EXP":
                        categorie = 'importExport'
                        if line.portnet_id:
                            portnet_id = line.portnet_id or ''
                        else:
                            raise osv.except_osv(_('Error!'), _(
                                "Ce Client N'est Pas Syncroniser Avec Le Guichet Unique"))
                        desactivation = 'true'
                        data = messagetemplateactivation.substitute(login=login, pwd=pwd, hmac=hmac,
                                                                    categorie=categorie, id_portnet=portnet_id,
                                                                    desactivation=desactivation)
                        future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                    if line.categ_id.code == "T":
                        categorie = 'transitaire'
                        if line.portnet_id:
                            portnet_id = line.portnet_id or ''
                        else:
                            raise osv.except_osv(_('Error!'), _(
                                "Ce Client N'est Pas Syncroniser Avec Le Guichet Unique"))
                        desactivation = 'true'
                        data = messagetemplateactivation.substitute(login=login, pwd=pwd, hmac=hmac,
                                                                    categorie=categorie, id_portnet=portnet_id,
                                                                    desactivation=desactivation)
                        future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                    if line.categ_id.code == "CONS":
                        categorie = 'consignataire'
                        if line.portnet_id:
                            portnet_id = line.portnet_id or ''
                        else:
                            raise osv.except_osv(_('Error!'), _(
                                "Ce Client N'est Pas Syncroniser Avec Le Guichet Unique"))
                        desactivation = 'true'
                        data = messagetemplateactivation.substitute(login=login, pwd=pwd, hmac=hmac,
                                                                    categorie=categorie, id_portnet=portnet_id,
                                                                    desactivation=desactivation)
                        future_to_line[executor.submit(self.fire_post_request, url, data, 120)] = line

                for future in concurrent.futures.as_completed(future_to_line):
                    try:
                        data = future.result()['response']
                        root = ET.fromstring(data.content)
                        for info in root.iter('info'):
                            info_list = (info.text).split(":")
                            if len(info_list) > 1:
                                self.portnet_id = int(info_list[1])
                            self.response_portnet = info.text
                    except Exception as exc:
                        raise exceptions.ValidationError("Problème de Connexion GU")
                date_format = '%Y-%m-%d'
                today = (datetime.datetime.today()).strftime(date_format)
                d1 = datetime.datetime.strptime(today, date_format)
                now = fields.Datetime.now()
                vals = {
                    'name': "Désactivation du Profil " + str(self.name),
                    'time':now,
                    'date': d1,
                    'partner_id': self.id,
                    'categ_id': self.categ_id.id,
                    'state': 'desactivation',
                }
                self.env['compte.gu.operation.history'].create(vals)
                self.active_gu = False


      @api.model
      def _cron_actv_desac_comptes_gu(self):
          date_format = '%Y-%m-%d'
          today = (datetime.datetime.today()).strftime(date_format)
          d1 = datetime.datetime.strptime(today, date_format)
          contracts = self.env['res.contract'].search([('state', '=', 'pending'),('next_invoice_date', '<=', d1), ('compte_active', '=', True)])
          for contract in contracts:
              partner_id = contract.partner_id
              if partner_id.portnet_id >0 and partner_id.categ_id.auto_activation and partner_id.auto_activation:
                partner_id.desactiv_gu()
                contract.compte_active = False
              self._cr.commit()

          # date_format = '%Y-%m-%d'
          # today = (datetime.datetime.today()).strftime(date_format)
          # d1 = datetime.datetime.strptime(today, date_format)
          # partner_ids = self.search(
          #     [('customer', '=', True), ('portnet_id', '>', 0)])
          # for partner_id in partner_ids:
          #     due_invoices = self.env['account.invoice'].search(
          #         [('partner_id', '=', partner_id.id), ('state', '=', 'open'), ('contract_id', '!=', False),
          #          ('flag_0_day_contract_mail', '=', False), ('user_id', '=', SUPERUSER_ID)], order="date_invoice desc")
          #     open_contracts = self.env['res.contract'].search(
          #         [('partner_id', '=', partner_id.id), ('state', '=', 'pending')])
          #     print "I al here"
          #     if open_contracts:
          #         if due_invoices:
          #             last_invoice = due_invoices[0]
          #             date_last_invoice = last_invoice.date_invoice
          #             d2 = datetime.datetime.strptime(date_last_invoice, date_format)
          #             daysDiff = (d2 - d1).days
          #             if daysDiff > 60:
          #                 print "Désactivation du Partenaire ", partner_id.name, " Il n'a pas payé sa dernière facture N° ", last_invoice.number, " Daté de ", last_invoice.date_invoice
          #                 #partner_id.desactiv_gu()
          #                 vals = {
          #                     'name': "Activation du Profil " + str(partner_id.name),
          #                     'date': d1,
          #                     'partner_id': partner_id.id,
          #                     'state': 'desactivation',
          #                 }
          #                 self.env['compte.gu.operation.history'].create(vals)
          #                 #self._cr.commit()
          #             else:
          #                 print "Activation du Partenaire ", partner_id.name
          #                 #partner_id.activ_gu()
          #                 vals = {
          #                     'name': "Activation du Profil " + str(partner_id.name),
          #                     'date': d1,
          #                     'partner_id': partner_id.id,
          #                     'state': 'activation',
          #                 }
          #                 self.env['compte.gu.operation.history'].create(vals)
          #                 #self._cr.commit()
          #         else:
          #             print "Activation du Partenaire ", partner_id.name
          #             #partner_id.activ_gu()
          #             vals = {
          #                 'name': "Activation du Profil " + str(partner_id.name),
          #                 'date': d1,
          #                 'partner_id': partner_id.id,
          #                 'state': 'activation',
          #             }
          #             self.env['compte.gu.operation.history'].create(vals)
          #             #self._cr.commit()
          #     else:
          #
          #         print "Désactivation du Partenaire ", partner_id.name, " Il n'a pas payé sa dernière facture N° ", last_invoice.number, " Daté de ", last_invoice.date_invoice
          #         #partner_id.desactiv_gu()
          #         vals = {
          #             'name': "Activation du Profil " + str(partner_id.name),
          #             'date': d1,
          #             'partner_id': partner_id.id,
          #             'state': 'desactivation',
          #         }
          #         self.env['compte.gu.operation.history'].create(vals)
          #         #self._cr.commit()


class BureauDouanier(models.Model):
      _name = 'bureau.douanier'

      port = fields.Char(string='Port')
      bureau_douanier = fields.Char(string='Bureau Douanier')
      autorisation_adii = fields.Char(string='Autorisation ADII')
      partner_id = fields.Many2one('res.partner',string='Partner')


class UserPortnet(models.Model):
      _name='user.portnet'
      _inherit = 'mail.thread'

      user_portnet = fields.Integer(string='Utilisateur Guichet Unique')
      first_name = fields.Char(string='Nom utilisateur guichet unique')
      last_name =  fields.Char(string='Prénom utilisateur guichet unique')
      cin = fields.Char(string="CIN")
      expiration_cin = fields.Date(string="Date Expiration CIN")
      domiciliation_cin = fields.Char(string="Domiciliation CIN")
      email = fields.Char(string='Email')
      partner_id = fields.Many2one('res.partner',string='Profil')
      portnet_id = fields.Integer(string='ID PORTNET',readonly=True)
      response_portnet = fields.Text(string='Reponse PORTNET',readonly=True)

class CompteGUOperationsHistory(models.Model):
    _name = 'compte.gu.operation.history'

    name = fields.Char(string=u'Libellé')
    time = fields.Datetime(string='Date')
    date=fields.Date(string="Date")
    categ_id = fields.Many2one('res.partner.category', string='Catégorie', required=False)
    partner_id = fields.Many2one('res.partner', string='Client')
    state = fields.Selection(string="Etat", selection=[('activation', 'Activation'), ('desactivation', 'Désactivation')])
    user_id = fields.Many2one('res.users', string='Utilisateur',default=lambda self: self.env.user)
