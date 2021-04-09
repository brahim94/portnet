# -*- coding: utf-8 -*-

import json
import logging
import requests
import base64
import datetime
import time
from openerp import api, fields, models, _
from dateutil.relativedelta import relativedelta
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import xmltodict
except:
    _logger.debug('xmltodict libraries not available. Please install "xmltodict"\
                 python package by "pip install xmltodict".')


class ResContract(models.Model):
    _inherit = 'res.contract'

    @api.model
    def create_subscription(self, values):
        subscription_id = False
        if values:

            ### Validate Data
            if not values.get('name'):
                return {'faultCode': 0, 'faultString': 'N° Souscriptions is required.'}
            if not values.get('template_id'):
                return {'faultCode': 0, 'faultString': 'Package is required.'}
            if not values.get('state'):
                return {'faultCode': 0, 'faultString': 'State is required.'}
            if not values.get('date_start'):
                return {'faultCode': 0, 'faultString': 'Date début is required.'}
            if not values.get('date'):
                return {'faultCode': 0, 'faultString': 'Date fin is required.'}
            if not values.get('partner_categ_id'):
                return {'faultCode': 0, 'faultString': "Rôle de l'opérateur is required."}
            if not values.get('partner_id'):
                return {'faultCode': 0, 'faultString': 'Opérateur is required.'}
            if not values.get('date_create'):
                return {'faultCode': 0, 'faultString': 'Create Date is required.'}

            ### Find Data From DB
            template_id = self.search([('name', '=', values['template_id']), ('type_contract', '=', 'package'), ('is_template', '=', True)], limit=1)
            if not template_id:
                return {'faultCode': 0, 'faultString': 'template_id doesn’t exist in Odoo db'}

            partner_categ_id = self.env['res.partner.category'].search([('code', '=', values['partner_categ_id'])], limit=1)
            if not partner_categ_id:
                return {'faultCode': 0, 'faultString': "partner_categ_id doesn’t exist in Odoo db"}

            partner_id = self.env['res.partner'].search([('code', '=', values['partner_id']), ('categ_id', '=', partner_categ_id.id), ('customer', '=', True)], limit=1)
            if not partner_id:
                return {'faultCode': 0, 'faultString': 'partner_id doesn’t exist in Odoo db'}

            ### A = pending
            ### D = draft
            state = False
            if values['state'] == 'A':
                state = 'pending'
            elif values['state'] == 'D':
                state = 'draft'
            else:
                return {'faultCode': 0, 'faultString': 'state doesn’t exist in Odoo db'}

            date_start = str(values['date_start']).strip()
            date = str(values['date']).strip()
            date_create = str(values['date_create']).strip()
            next_invoice_date = fields.Date.from_string(date_start) + relativedelta(months=template_id.periodicity_id.nb_months)

            subscription_id = self.with_context(default_type_contract='package', default_is_template=False).create({
                    ### API Fields
                    'name': values['name'],
                    'template_id': template_id.id if template_id else False,
                    'date_start': date_start,
                    'date': date,
                    'add_balance': values.get('add_balance') or 0,
                    'partner_categ_id': partner_categ_id.id if partner_categ_id else False,
                    'partner_id': partner_id.id if partner_id else False,
                    'date_create_portnet': date_create,
                    'state': state,
                    
                    ### Default Package Fields
                    'product_id': template_id.product_id.id,
                    'product_category_id': template_id.product_category_id.id,
                    'periodicity_id': template_id.periodicity_id.id,
                    'tacite': template_id.tacite,
                    'currency_id': template_id.currency_id.id,
                    'amount': template_id.amount,
                    'transaction_no': template_id.transaction_no,
                    'first_invoice_date': date_start,
                    'next_invoice_date': next_invoice_date,
                    'anticipated_invoice_date': next_invoice_date,
                })
            subscription_id.onchange_template_id()
            subscription_id.message_post(body=_("Record created by API Services"))
        if subscription_id:
            return {'success': subscription_id.id}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}

    @api.model
    def update_subscription(self, values):
        subscription_id = False
        if values:

            ### Validate Data
            if not values.get('name'):
                return {'faultCode': 0, 'faultString': 'N° Souscriptions is required.'}
            if not values.get('comment'):
                return {'faultCode': 0, 'faultString': 'Comment is required.'}
            if not values.get('date_write'):
                return {'faultCode': 0, 'faultString': 'Update Date is required.'}

            ### Find Data From DB
            subscription_id = self.search([('name', '=', values['name']), ('type_contract', '=', 'package'), ('is_template', '=', False)], limit=1)
            if not subscription_id:
                return {'faultCode': 0, 'faultString': 'Subscription doesn’t exist in Odoo db'}

            vals = {}
            
            if values.get('date_start'):
                vals.update({'date_start': str(values['date_start']).strip()})
            
            if values.get('date'):
                vals.update({'date': str(values['date']).strip()})

            if values.get('add_balance'):
                vals.update({'add_balance': values['add_balance'] or 0})

            t = time.strptime(str(values['date_write']).strip(), "%Y-%m-%dT%H:%M:%S")
            date_write = datetime.datetime(*tuple(t)[:7])

            # date_write = str(values['date_write']).strip()
            vals.update({'date_write_portnet': date_write})

            if values.get('state'):
                if values['state'] == 'A':
                    vals.update({'state': 'pending'})
                elif values['state'] == 'S':
                    vals.update({'state': 'suspend'})
                elif values['state'] == 'E':
                    vals.update({'state': 'expire'})
                elif values['state'] == 'C':
                    vals.update({'state': 'closed'})

            # vals.update({'description_package': values.get('comment')})

            subscription_id.write(vals)
            subscription_id.message_post(body=_("Record updated by API Services"))
            subscription_id.message_post(body=_(values.get('comment').strip()))

        if subscription_id:
            return {'success': subscription_id.id}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}

    def master_tag_start(self, tag):
        data = "<%s xmlns=\"http://www.portnet.ma/nouvelleTarification\">" % tag
        return data

    def sub_tag_start(self, tag):
        data = "<%s>" % tag
        return data

    def tag_end(self, tag):
        data = "</%s>" % tag
        return data

    def new_line(self):
        return '\n'

    def get_tab(self):
        return ''.ljust(4)

    def get_tranches_lines(self, line_ids):
        lines = ''
        for line in line_ids:
            lines += ''.join([
                self.sub_tag_start('tranches'),
                self.sub_tag_start('de'), (line.tranche_de_no or ''), self.tag_end('de'), self.new_line(), self.get_tab(),
                self.sub_tag_start('a'), (line.tranche_a_no or ''), self.tag_end('a'), self.new_line(), self.get_tab(),
                self.sub_tag_start('frais'), (line.frais_de_services or ''), self.tag_end('frais'), self.new_line(), self.get_tab(),
                self.tag_end('tranches'),
                ])
        return lines

    @api.multi
    def action_sync_GU(self):
        company_id = self.env.user.company_id
        url = (("%s/crm/nouvelleTarification/updateSouscription") % (company_id.ip_address))

        # payload = "<souscription xmlns=\"http://www.portnet.ma/nouvelleTarification\">\n    <identifiant>S000545</identifiant>\n    <codePackage>POS-AGM-111125</codePackage>\n    <debutValidite>2020-05-30T09:00:00</debutValidite>\n    <finValidite>2020-06-30T09:00:00</finValidite>\n    <soldeSupplementaire>400</soldeSupplementaire>\n    <statut>ACTIVE</statut>\n    <typeOperateur>IMPEXP</typeOperateur>\n    <codeOperateur>3861</codeOperateur>\n</souscription >"
        headers = {
            'authorization': "Basic %s" % (base64.b64encode(("%s:%s" % (company_id.user_id, company_id.password)).encode())).decode(),
            'content-type': "application/xml",
        }
        
        payload = ''.join([
            self.master_tag_start('souscription'), self.new_line(), self.get_tab(),
            self.sub_tag_start('identifiant'), (self.name or ''), self.tag_end('identifiant'), self.new_line(), self.get_tab(),
            self.sub_tag_start('debutValidite'), (fields.Datetime.from_string(self.date_start).strftime("%Y-%m-%dT%H:%M:%S")), self.tag_end('debutValidite'), self.new_line(), self.get_tab(),
            self.sub_tag_start('finValidite'), (fields.Datetime.from_string(self.date).strftime("%Y-%m-%dT%H:%M:%S")), self.tag_end('finValidite'), self.new_line(), self.get_tab(),
            self.sub_tag_start('dateModification'), (fields.Datetime.from_string(fields.Datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")), self.tag_end('dateModification'), self.new_line(), self.get_tab(),
            self.sub_tag_start('motif'), (str(self.description_package) or ''), self.tag_end('motif'), self.new_line(), self.get_tab(),
            self.tag_end('souscription'),
            ])

        response = requests.request("POST", url, headers=headers, data=payload)
        
        res = json.loads(json.dumps(xmltodict.parse(response.text, process_namespaces=True)))
        if response.status_code != 200:
            message = ''
            description = ''
            guid = ''
            res = json.loads(json.dumps(xmltodict.parse(response.text, process_namespaces=True)))
            if res and res.get('http://www.portnet.ma/nouvelleTarification:reponse') and res.get('http://www.portnet.ma/nouvelleTarification:reponse').get('http://www.portnet.ma/nouvelleTarification:description'):
                message = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:message']
                description = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:description']
                guid = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:guid']
            _logger.warning("\nERROR MESSAGE: \n\n %s \n\n" % str(response.text))
            raise ValidationError("%s \n\n %s \nGUID: %s" % (message, description, guid))
        self.write({'date_write_portnet': fields.Datetime.now(), 'date_sync_portnet': fields.Datetime.now()})

        return True

    @api.multi
    def action_suspend(self):
        company_id = self.env.user.company_id
        url = (("%s/crm/nouvelleTarification/suspendSouscription") % (company_id.ip_address))

        # payload = "<souscription xmlns=\"http://www.portnet.ma/nouvelleTarification\">\n    <identifiant>S000545</identifiant>\n    <codePackage>POS-AGM-111125</codePackage>\n    <debutValidite>2020-05-30T09:00:00</debutValidite>\n    <finValidite>2020-06-30T09:00:00</finValidite>\n    <soldeSupplementaire>400</soldeSupplementaire>\n    <statut>ACTIVE</statut>\n    <typeOperateur>IMPEXP</typeOperateur>\n    <codeOperateur>3861</codeOperateur>\n</souscription >"
        headers = {
            'authorization': "Basic %s" % (base64.b64encode(("%s:%s" % (company_id.user_id, company_id.password)).encode())).decode(),
            'content-type': "application/xml",
        }
        
        payload = ''.join([
            self.master_tag_start('souscription'), self.new_line(), self.get_tab(),
            self.sub_tag_start('identifiant'), (self.name or ''), self.tag_end('identifiant'), self.new_line(), self.get_tab(),
            self.sub_tag_start('statut'), ('SUSPENDU'), self.tag_end('statut'), self.new_line(), self.get_tab(),
            self.sub_tag_start('dateSuspension'), (fields.Datetime.from_string(fields.Datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")), self.tag_end('dateSuspension'), self.new_line(), self.get_tab(),
            self.sub_tag_start('motif'), (str(self.description_package) or ''), self.tag_end('motif'), self.new_line(), self.get_tab(),
            self.tag_end('souscription'),
            ])

        response = requests.request("POST", url, headers=headers, data=payload)
        
        res = json.loads(json.dumps(xmltodict.parse(response.text, process_namespaces=True)))
        if response.status_code != 200:
            message = ''
            description = ''
            guid = ''
            res = json.loads(json.dumps(xmltodict.parse(response.text, process_namespaces=True)))
            if res and res.get('http://www.portnet.ma/nouvelleTarification:reponse') and res.get('http://www.portnet.ma/nouvelleTarification:reponse').get('http://www.portnet.ma/nouvelleTarification:description'):
                message = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:message']
                description = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:description']
                guid = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:guid']
            _logger.warning("\nERROR MESSAGE: \n\n %s \n\n" % str(response.text))
            raise ValidationError("%s \n\n %s \nGUID: %s" % (message, description, guid))
        self.write({'date_sync_portnet': fields.Datetime.now(), 'state': 'suspend'})
        
        return True

    @api.model
    def create_package(self, values):
        package_id = False
        if values:

            vals = {}
            Currency = self.env['res.currency']
            Product = self.env['product.product']
            ProductCategory = self.env['product.category']
            PartnerCategory = self.env['res.partner.category']
            Periodicity = self.env['res.periodicity']

            ### Validate Data
            if not values.get('name'):
                return {'faultCode': 0, 'faultString': 'Code package is required.'}
            if not values.get('partner_categ_id'):
                return {'faultCode': 0, 'faultString': "Rôle de l'opérateur is required."}
            if not values.get('active_package'):
                return {'faultCode': 0, 'faultString': 'Active Package status is required.'}
            if not values.get('criteria_factures'):
                return {'faultCode': 0, 'faultString': 'Critére de facturation is required.'}
            if not values.get('parameter_decompte'):
                return {'faultCode': 0, 'faultString': 'Paramétre de décompte is required.'}
            if not values.get('type_paiment'):
                return {'faultCode': 0, 'faultString': 'Type paiement is required.'}
            if values.get('transaction_no') and values['transaction_no'] == 'transaction_limit' and not values.get('transaction_no_limit'):
                return {'faultCode': 0, 'faultString': 'Nombre de transactions is required.'}
            if not values.get('periodicity_id'):
                return {'faultCode': 0, 'faultString': 'Périodicité is required.'}
            if not values.get('debut_validate'):
                return {'faultCode': 0, 'faultString': 'Debut de validité is required.'}
            if not values.get('validate_package'):
                return {'faultCode': 0, 'faultString': 'Validité du package is required.'}
            # if not values.get('tacite'):
            #     return {'faultCode': 0, 'faultString': 'Tacite de reconduction is required.'}
            if not values.get('type_service'):
                return {'faultCode': 0, 'faultString': 'Type de frais is required.'}
            if not values.get('date_create'):
                return {'faultCode': 0, 'faultString': 'Create Date is required.'}
            

            ### Find Data From DB
            currency_id = Currency.search([('name', '=', 'MAD')], limit=1)
            if not currency_id:
                return {'faultCode': 0, 'faultString': 'Currency doesn’t exist in Odoo db'}

            product_category_id = self.env.ref('product.product_category_all')
            if not product_category_id:
                product_category_id = ProductCategory.search([('name', '=', 'All')], limit=1)
                if not product_category_id:
                    return {'faultCode': 0, 'faultString': 'Product Category doesn’t exist in Odoo db'}

            product_id = Product.search([('name', '=', values['name'])], limit=1)
            if not product_id:
                product_id = Product.with_context(default_type='service', default_is_package=True, default_category_id=product_category_id.id).create({
                        'name': values['name'],
                    })

            partner_categ_id = PartnerCategory.search([('code', '=', values['partner_categ_id'])], limit=1)
            if not partner_categ_id:
                return {'faultCode': 0, 'faultString': "partner_categ_id doesn’t exist in Odoo db"}

            month = 0
            if values['periodicity_id'] == 'Mensuel':
                month = 1
            elif values['periodicity_id'] == 'Trimestriel':
                month = 3
            elif values['periodicity_id'] == 'Semestriel':
                month = 6
            elif values['periodicity_id'] == 'Annuel':
                month = 12

            periodicity_id = Periodicity.search([('nb_months', '=', month)], limit=1)
            if not periodicity_id:
                return {'faultCode': 0, 'faultString': 'periodicity_id doesn’t exist in Odoo db'}

            criteria_factures = False
            if values['criteria_factures'] == "Titre d'importation":
                criteria_factures = 'enable'
            elif values['criteria_factures'] == "Escale":
                criteria_factures = 'disable'

            parameter_decompte = False
            if values['parameter_decompte'] == "Envoi pour domiciliation":
                parameter_decompte = 'enable'
            elif values['parameter_decompte'] == "Envoi du manifeste":
                parameter_decompte = 'disable'

            if values['type_service'] == 'fix' and not values.get('service_fee'):
                return {'faultCode': 0, 'faultString': 'service_fee is mandatory.'}
            elif values['type_service'] == 'tranches' and not values.get('type_service_line_ids'):
                return {'faultCode': 0, 'faultString': 'service_lines is mandatory.'}

            if values.get('type_service_line_ids'):
                service_lines = []
                for line in values['type_service_line_ids']:
                    service_lines.append((0, 0, {'tranche_de_no': line[0], 'tranche_a_no': line[1], 'frais_de_services': line[2]}))
                vals.update({'type_service_line_ids': service_lines})

            date_create = str(values['date_create']).strip()

            if values.get('transaction_no'):
                vals.update({'transaction_no': values['transaction_no']})

            vals.update({
                    'name': values['name'],
                    'currency_id': currency_id.id,
                    'product_category_id': product_category_id.id,
                    'product_id': product_id.id,
                    'partner_categ_id': partner_categ_id.id,
                    'active_package': values['active_package'],
                    'criteria_factures': criteria_factures,
                    'parameter_decompte': parameter_decompte,
                    'type_paiment': values['type_paiment'],
                    # 'transaction_no': values['transaction_no'],
                    'transaction_no_limit': values.get('transaction_no_limit'),
                    'amount': values.get('amount'),
                    'periodicity_id': periodicity_id.id,
                    'debut_validate': values['debut_validate'],
                    'validate_package': values['validate_package'],
                    'tacite': values['tacite'],
                    'type_service': values['type_service'],
                    'service_fee': values.get('service_fee'),
                    'description_package': values.get('description_package'),
                    'date_create_portnet': date_create,
                })

            package_id = self.with_context(default_type_contract='package', default_is_template=True).create(vals)
            package_id.message_post(body=_("Record created by API Services"))
        
        if package_id:
            return {'success': package_id.id}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}

    @api.model
    def update_package(self, values):
        package_id = False
        if values:

            vals = {}
            PartnerCategory = self.env['res.partner.category']
            Periodicity = self.env['res.periodicity']

            ### Validate Data
            if not values.get('name'):
                return {'faultCode': 0, 'faultString': 'Code package is required.'}
            if not values.get('comment'):
                return {'faultCode': 0, 'faultString': 'Comment is required.'}
            if not values.get('date_write'):
                return {'faultCode': 0, 'faultString': 'Update Date is required.'}

            package_id = self.search([('name', '=', values['name']), ('type_contract', '=', 'package'), ('is_template', '=', True)], limit=1)
            if not package_id:
                return {'faultCode': 0, 'faultString': 'Package doesn’t exist in Odoo db'}

            ### Find Data From DB
            if values.get('partner_categ_id'):
                partner_categ_id = PartnerCategory.search([('code', '=', values['partner_categ_id'])], limit=1)
                if not partner_categ_id:
                    return {'faultCode': 0, 'faultString': "partner_categ_id doesn’t exist in Odoo db"}
                vals.update({'partner_categ_id': partner_categ_id.id})

            if values.get('active_package'):
                vals.update({'active_package': values['active_package']})

            if values.get('criteria_factures'):
                if values['criteria_factures'] == "Titre d'importation":
                    vals.update({'criteria_factures': 'enable'})
                elif values['criteria_factures'] == "Escale":
                    vals.update({'criteria_factures': 'disable'})

            if values.get('parameter_decompte'):
                if values['parameter_decompte'] == "Envoi pour domiciliation":
                    vals.update({'parameter_decompte': 'enable'})
                elif values['parameter_decompte'] == "Envoi du manifeste":
                    vals.update({'parameter_decompte': 'disable'})

            if values.get('type_paiment'):
                vals.update({'type_paiment': values['type_paiment']})

            if values.get('transaction_no'):
                vals.update({'transaction_no': values['transaction_no']})

            if values.get('transaction_no_limit'):
                vals.update({'transaction_no_limit': values['transaction_no_limit']})

            if values.get('amount'):
                vals.update({'amount': values['amount']})

            if values.get('periodicity_id'):
                month = 0
                if values['periodicity_id'] == 'Mensuel':
                    month = 1
                elif values['periodicity_id'] == 'Trimestriel':
                    month = 3
                elif values['periodicity_id'] == 'Semestriel':
                    month = 6
                elif values['periodicity_id'] == 'Annuel':
                    month = 12

                periodicity_id = Periodicity.search([('nb_months', '=', month)], limit=1)
                if not periodicity_id:
                    return {'faultCode': 0, 'faultString': 'periodicity_id doesn’t exist in Odoo db'}
                vals.update({'periodicity_id': periodicity_id.id})

            if values.get('debut_validate'):
                vals.update({'debut_validate': values['debut_validate']})

            if values.get('validate_package'):
                vals.update({'validate_package': values['validate_package']})

            if values.get('type_service'):
                if values['type_service'] == 'fix' and not values.get('service_fee'):
                    return {'faultCode': 0, 'faultString': 'service_fee is mandatory.'}
                elif values['type_service'] == 'tranches' and not values.get('type_service_line_ids'):
                    return {'faultCode': 0, 'faultString': 'service_lines is mandatory.'}
                vals.update({'type_service': values['type_service']})

            if values.get('service_fee'):
                vals.update({'service_fee': values['service_fee']})

            if values.get('type_service_line_ids'):
                service_lines = []
                for line in values['type_service_line_ids']:
                    service_lines.append((0, 0, {'tranche_de_no': line[0], 'tranche_a_no': line[1], 'frais_de_services': line[2]}))
                package_id.type_service_line_ids.unlink()
                vals.update({'type_service_line_ids': service_lines})

            if values.get('description_package'):
                vals.update({'description_package': values['description_package']})

            date_write = str(values['date_write']).strip()
            vals.update({'date_write_portnet': date_write, 'tacite': values.get('tacite')})

            package_id.write(vals)
            package_id.message_post(body=_("Record updated by API Services"))
            package_id.message_post(body=_((values['comment']).strip()))
        
        if package_id:
            return {'success': package_id.id}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}
            

    @api.multi
    def create_package_export(self):
        package_code = False
        contract_id = self
        company_id = self.env.user.company_id
        url = (("%s/crm/nouvelleTarification/createPackage") % (company_id.ip_address))
        code_url = ("%s/crm/nouvelleTarification/identifiantPackage?roleOperateur=%s&typePaiement=%s") % (company_id.ip_address, str(contract_id.partner_categ_id.code), str(contract_id.type_paiment))

        # payload = "<souscription xmlns=\"http://www.portnet.ma/nouvelleTarification\">\n    <identifiant>S000545</identifiant>\n    <codePackage>POS-AGM-111125</codePackage>\n    <debutValidite>2020-05-30T09:00:00</debutValidite>\n    <finValidite>2020-06-30T09:00:00</finValidite>\n    <soldeSupplementaire>400</soldeSupplementaire>\n    <statut>ACTIVE</statut>\n    <typeOperateur>IMPEXP</typeOperateur>\n    <codeOperateur>3861</codeOperateur>\n</souscription >"
        headers = {
            'authorization': "Basic %s" % (base64.b64encode(("%s:%s" % (company_id.user_id, company_id.password)).encode())).decode(),
            'content-type': "application/xml",
        }

        ### Get Package Code
        response_code = requests.request("GET", code_url, headers=headers)

        res_code = json.loads(json.dumps(xmltodict.parse(response_code.text, process_namespaces=True)))
        result_sub_code = json.loads(json.dumps(xmltodict.parse(response_code.text, process_namespaces=True)))
        if response_code.status_code == 200:
            if result_sub_code and result_sub_code.get('http://www.portnet.ma/nouvelleTarification:reponse') and result_sub_code.get('http://www.portnet.ma/nouvelleTarification:reponse').get('http://www.portnet.ma/nouvelleTarification:message'):
                package_code = result_sub_code['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:message']
        else:
            message_code = ''
            description_code = ''
            guid_code = ''
            if result_sub_code and result_sub_code.get('http://www.portnet.ma/nouvelleTarification:reponse') and result_sub_code.get('http://www.portnet.ma/nouvelleTarification:reponse').get('http://www.portnet.ma/nouvelleTarification:description'):
                message_code = result_sub_code['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:message']
                description_code = result_sub_code['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:description']
                guid_code = result_sub_code['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:guid']
            _logger.warning("\nERROR MESSAGE: \n\n %s \n\n" % str(response_code.text))
            raise ValidationError("%s \n\n %s \nGUID: %s" % (message_code, description_code, guid_code))

        ### Create Package After getting package number
        payload = ''.join([
            contract_id.master_tag_start('package'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('code'), (package_code), contract_id.tag_end('code'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('statut'), ('Actif'), contract_id.tag_end('statut'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('roleOperateur'), (contract_id.partner_categ_id.code or ''), contract_id.tag_end('roleOperateur'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('critereFacturation'), str(dict(self._fields['criteria_factures'].selection).get(contract_id.criteria_factures)), contract_id.tag_end('critereFacturation'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('parametreDecompte'), str(dict(self._fields['parameter_decompte'].selection).get(contract_id.parameter_decompte)), contract_id.tag_end('parametreDecompte'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('reconduction'), ('1' if contract_id.tacite else ''), contract_id.tag_end('reconduction'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('typePaiement'), (contract_id.type_paiment or ''), contract_id.tag_end('typePaiement'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('transactionAutorisee'), (contract_id.transaction_no or ''), contract_id.tag_end('transactionAutorisee'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('nbreTransactions'), (str(contract_id.transaction_no_limit) or ''), contract_id.tag_end('nbreTransactions'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('abonnementBase'), (str(contract_id.amount) or ''), contract_id.tag_end('abonnementBase'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('periodicite'), (contract_id.periodicity_id.name or ''), contract_id.tag_end('periodicite'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('validite'), (contract_id.validate_package or ''), contract_id.tag_end('validite'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('debutValidite'), (contract_id.debut_validate or ''), contract_id.tag_end('debutValidite'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('typeService'), (contract_id.type_service or ''), contract_id.tag_end('typeService'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('fraisService'), (str(contract_id.service_fee) or ''), contract_id.tag_end('fraisService'), contract_id.new_line(), contract_id.get_tab(),
            (contract_id.get_tranches_lines(contract_id.type_service_line_ids)),
            contract_id.sub_tag_start('dateCreation'), (fields.Datetime.from_string(contract_id.date_create_portnet or fields.Datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")), contract_id.tag_end('dateCreation'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.sub_tag_start('description'), (contract_id.description_package or ''), contract_id.tag_end('description'), contract_id.new_line(), contract_id.get_tab(),
            contract_id.tag_end('package'),
            ])
        
        response = requests.request("POST", url, headers=headers, data=payload)

        res = json.loads(json.dumps(xmltodict.parse(response.text, process_namespaces=True)))
        if response.status_code != 200:
            message = ''
            description = ''
            guid = ''
            res = json.loads(json.dumps(xmltodict.parse(response.text, process_namespaces=True)))
            if res and res.get('http://www.portnet.ma/nouvelleTarification:reponse') and res.get('http://www.portnet.ma/nouvelleTarification:reponse').get('http://www.portnet.ma/nouvelleTarification:description'):
                message = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:message']
                description = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:description']
                guid = res['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:guid']
            _logger.warning("\nERROR MESSAGE: \n\n %s \n\n" % str(response.text))
            raise ValidationError("%s \n\n %s \nGUID: %s" % (message, description, guid))
        else:
            contract_id.write({'name': package_code, 'date_create_portnet': fields.Datetime.now(), 'date_sync_portnet': fields.Datetime.now()})
        return True

    @api.model
    def create(self, values):
        res = super(ResContract, self).create(values)
        if self._context.get('default_is_template') and self._context['default_is_template'] == True and self._context.get('default_type_contract') and self._context['default_type_contract'] == 'package':
            res.create_package_export()
        return res