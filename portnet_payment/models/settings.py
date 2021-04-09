# -*- encoding: utf-8 -*-
from openerp import models, fields,  api, _, exceptions
from openerp.exceptions import except_orm, Warning, RedirectWarning
import psycopg2
import sys
import os
import pwd

class folder_path_setting(models.Model):
    _inherit = 'folder.path.setting'

    cheque_state_folder=fields.Char(string="Réception des états des chéques",required=False,help="Chemin du dossier qui contient les fichier csv des banques descrivant les états des chéques : payé ou impayé")
    etebac3_folder=fields.Char(string="Réception ETEBAC3",required=False,help="Chemin du dossier contenant les fichiers ETEBAC3")
    odoo_payments_folder=fields.Char(string="Dépot Paiements",required=False,help="Chemin du dossier contenant les paiements clients saisies sur Odoo")
    portnet_payments_folder=fields.Char(string="Réception Paiements",required=False,help="Chemin du dossier contenant les paiements clients issus de Portnet")

    @api.multi
    def get_cheque_folder(self,cron=False):
        exchange_folder_id=self.search([('state','=','confirmed')])
        if exchange_folder_id :
                exchange_folder=exchange_folder_id.exchange_folder
                dirpath=exchange_folder+"/"+exchange_folder_id.cheque_state_folder
                if not os.path.exists(exchange_folder) or  not os.path.exists(dirpath) :
                    output="Il n'existe pas un dossier des échanges avec les banques  dans le serveur"
                    if cron :
                         code='exchange_folder_error'
                         type="exchange"
                         self.env['report.exception'].set_exception(code,output)
                         return False
                    else :
                        raise Warning(output)
                return dirpath
        else :
             output="Il n'existe pas un dossier des échanges SI Portnet confirmé sur le système"
             if cron :
                         code='exchange_folder_error'
                         type="exchange"
                         self.env['report.exception'].set_exception(code,output)
                         return False
             else :
                    raise Warning(output)

    @api.multi
    def get_etebac3_folder(self,cron=False):
        exchange_folder_id=self.search([('state','=','confirmed')])
        if exchange_folder_id :
                exchange_folder=exchange_folder_id.exchange_folder
                dirpath=exchange_folder+"/"+exchange_folder_id.etebac3_folder
                if not os.path.exists(exchange_folder) or  not os.path.exists(dirpath) :
                    output="Il n'existe pas un dossier des échanges ETEBAC3  dans le serveur"
                    if cron :
                         code='exchange_folder_error'
                         type="exchange"
                         self.env['report.exception'].set_exception(code,output)
                         return False
                    else :
                        raise Warning(output)
                return dirpath
        else :
             output="Il n'existe pas un dossier des échanges SI Portnet confirmé sur le système"
             if cron :
                         code='exchange_folder_error'
                         type="exchange"
                         self.env['report.exception'].set_exception(code,output)
                         return False
             else :
                    raise Warning(output)

    @api.multi
    def get_odoo_payments_folder(self,cron=False):
        exchange_folder_id=self.search([('state','=','confirmed')])
        if exchange_folder_id :
                exchange_folder=exchange_folder_id.exchange_folder
                dirpath=exchange_folder+"/"+exchange_folder_id.odoo_payments_folder
                if not os.path.exists(exchange_folder) or  not os.path.exists(dirpath) :
                    output="Il n'existe pas un dossier de dépôt des retours de paiements clients Odoo dans le serveur"
                    if cron :
                         code='exchange_folder_error'
                         type="exchange"
                         self.env['report.exception'].set_exception(code,output)
                         return False
                    else :
                        raise Warning(output)
                return dirpath
        else :
             output="Il n'existe pas un dossier des échanges SI Portnet confirmé sur le système"
             if cron :
                         code='exchange_folder_error'
                         type="exchange"
                         self.env['report.exception'].set_exception(code,output)
                         return False
             else :
                    raise Warning(output)

    @api.multi
    def get_portnet_payments_folder(self,cron=False):
        exchange_folder_id=self.search([('state','=','confirmed')])
        if exchange_folder_id :
                exchange_folder=exchange_folder_id.exchange_folder
                dirpath=exchange_folder+"/"+exchange_folder_id.portnet_payments_folder
                if not os.path.exists(exchange_folder) or  not os.path.exists(dirpath) :
                    output="Il n'existe pas un dossier de réception des paiements clients Portnet dans le serveur"
                    if cron :
                         code='exchange_folder_error'
                         type="exchange"
                         self.env['report.exception'].set_exception(code,output)
                         return False
                    else :
                        raise Warning(output)
                return dirpath
        else :
             output="Il n'existe pas un dossier des échanges SI Portnet confirmé sur le système"
             if cron :
                         code='exchange_folder_error'
                         type="exchange"
                         self.env['report.exception'].set_exception(code,output)
                         return False
             else :
                    raise Warning(output)



    @api.multi
    def action_confirm(self):
        try:
            directory=self.exchange_folder
            if not os.path.exists(directory):
                os.makedirs(directory)
                os.chmod(directory,0777)
            invoices_folder=directory+"/"+self.invoices_folder
            if not os.path.exists(invoices_folder):
                    os.makedirs(invoices_folder)
                    os.chmod(invoices_folder,0777)
            cheque_state_folder=directory+"/"+self.cheque_state_folder
            if not os.path.exists(cheque_state_folder):
                    os.makedirs(cheque_state_folder)
                    os.chmod(cheque_state_folder,0777)
            etebac3_folder=directory+"/"+self.etebac3_folder
            if not os.path.exists(etebac3_folder):
                    os.makedirs(etebac3_folder)
                    os.chmod(etebac3_folder,0777)
            odoo_payments_folder=directory+"/"+self.odoo_payments_folder
            if not os.path.exists(odoo_payments_folder):
                    os.makedirs(odoo_payments_folder)
                    os.chmod(odoo_payments_folder,0777)
            portnet_payments_folder=directory+"/"+self.portnet_payments_folder
            if not os.path.exists(portnet_payments_folder):
                    os.makedirs(portnet_payments_folder)
                    os.chmod(portnet_payments_folder,0777)
        except:
            raise exceptions.ValidationError("Création de répértoire impossible sur le chemin indiqué")
        self.state='confirmed'

folder_path_setting()