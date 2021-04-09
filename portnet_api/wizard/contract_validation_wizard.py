# -*- encoding: utf-8 -*-

import json
import logging
import requests
import base64
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import xmltodict
except:
    _logger.debug('xmltodict libraries not available. Please install "xmltodict"\
                 python package by "pip install xmltodict".')


class ContractValidationWizard(models.TransientModel):
    _inherit = 'contract.validation.wizard'

    @api.multi
    def action_confirm(self):
        result = super(ContractValidationWizard, self).action_confirm()

        if self.contract_id:
            contract_id = self.contract_id
            subscription_code = contract_id.name
            company_id = self.env.user.company_id
            if not subscription_code:
                url = (("%s/crm/nouvelleTarification/createSouscription") % (company_id.ip_address))
                code_url = (("%s/crm/nouvelleTarification/identifiantSouscription") % (company_id.ip_address))

                # payload = "<souscription xmlns=\"http://www.portnet.ma/nouvelleTarification\">\n    <identifiant>S000545</identifiant>\n    <codePackage>POS-AGM-111125</codePackage>\n    <debutValidite>2020-05-30T09:00:00</debutValidite>\n    <finValidite>2020-06-30T09:00:00</finValidite>\n    <soldeSupplementaire>400</soldeSupplementaire>\n    <statut>ACTIVE</statut>\n    <typeOperateur>IMPEXP</typeOperateur>\n    <codeOperateur>3861</codeOperateur>\n</souscription >"
                
                headers = {
                    'authorization': "Basic %s" % (base64.b64encode(("%s:%s" % (company_id.user_id, company_id.password)).encode())).decode(),
                    'content-type': "application/xml",
                }

                ### Get Subscription Code
                response_code = requests.request("POST", code_url, headers=headers)

                res_code = json.loads(json.dumps(xmltodict.parse(response_code.text, process_namespaces=True)))
                result_sub_code = json.loads(json.dumps(xmltodict.parse(response_code.text, process_namespaces=True)))
                if response_code.status_code == 200:
                    if result_sub_code and result_sub_code.get('http://www.portnet.ma/nouvelleTarification:reponse') and result_sub_code.get('http://www.portnet.ma/nouvelleTarification:reponse').get('http://www.portnet.ma/nouvelleTarification:message'):
                        subscription_code = result_sub_code['http://www.portnet.ma/nouvelleTarification:reponse']['http://www.portnet.ma/nouvelleTarification:message']
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

                ### Create Subscription After getting subscription number
                payload = ''.join([
                    contract_id.master_tag_start('souscription'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('identifiant'), (subscription_code), contract_id.tag_end('identifiant'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('codePackage'), (contract_id.template_id.name if contract_id.template_id else ''), contract_id.tag_end('codePackage'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('debutValidite'), (fields.Datetime.from_string(contract_id.date_start).strftime("%Y-%m-%dT%H:%M:%S")), contract_id.tag_end('debutValidite'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('finValidite'), (fields.Datetime.from_string(contract_id.date).strftime("%Y-%m-%dT%H:%M:%S")), contract_id.tag_end('finValidite'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('soldeSupplementaire'), str(contract_id.add_balance or 0), contract_id.tag_end('soldeSupplementaire'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('statut'), ('VALIDEE'), contract_id.tag_end('statut'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('typeOperateur'), (contract_id.partner_categ_id.code or ''), contract_id.tag_end('typeOperateur'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('codeOperateur'), (contract_id.partner_id.code or ''), contract_id.tag_end('codeOperateur'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.sub_tag_start('dateCreation'), (fields.Datetime.from_string(contract_id.date_create_portnet or fields.Datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")), contract_id.tag_end('dateCreation'), contract_id.new_line(), contract_id.get_tab(),
                    contract_id.tag_end('souscription'),
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

                contract_id.write({'name': subscription_code, 'date_create_portnet': fields.Datetime.now()})
            else:
                contract_id.action_sync_GU()
        
        return result
