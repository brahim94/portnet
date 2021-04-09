# -*- coding: utf-8 -*-
##############################################################################

from openerp import models, fields ,api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import os, os.path ,glob

class res_bank(models.Model):
    _inherit = "res.bank"

    bic=fields.Char('SWIFT', size=64, help="Sometimes called BIC or Swift.")
    check_unpaid=fields.Boolean('Vérification des chéques impayés')
    etebac3_file=fields.Boolean('Chargement des fichiers ETEBAC3')

    @api.constrains('bic')
    def _check_bic(self):
      res=self.search( [('bic','=',self.bic)] )
      if len(res) > 1:
        raise Warning("Le code SWIFT est unique par banque")

    @api.model
    def create(self, vals, context=None):
        if vals.get('check_unpaid', False) and  vals.get('bic', False) :
            dirpath=self.env["folder.path.setting"].get_cheque_folder()
            bank_folder=os.path.join(dirpath, vals['bic'])
            loaded_path=os.path.join(bank_folder, 'loaded')
            if not os.path.exists(bank_folder):
                os.makedirs(bank_folder)
                os.chmod(bank_folder,0777)
                os.makedirs(loaded_path)
                os.chmod(loaded_path,0777)

        if vals.get('etebac3_file', False) and  vals.get('bic', False) :
            dirpath=self.env["folder.path.setting"].get_etebac3_folder()
            bank_folder=os.path.join(dirpath, vals['bic'])
            loaded_path=os.path.join(bank_folder, 'loaded')
            print bank_folder
            if not os.path.exists(bank_folder):
                os.makedirs(bank_folder)
                os.chmod(bank_folder,0777)
                os.makedirs(loaded_path)
                os.chmod(loaded_path,0777)
        return super(res_bank, self).create( vals)

    @api.multi
    def write(self, vals, context=None):
        if self.check_unpaid :
            if  vals.get('bic', False) :
                folder_name=vals['bic']
            else :
                folder_name=self.bic
            dirpath=self.env["folder.path.setting"].get_cheque_folder()
            bank_folder=os.path.join(dirpath,folder_name )
            loaded_path=os.path.join(bank_folder, 'loaded')
            if not os.path.exists(bank_folder):
                os.makedirs(bank_folder)
                os.chmod(bank_folder,0777)
                os.makedirs(loaded_path)
                os.chmod(loaded_path,0777)

        if self.etebac3_file :
            if  vals.get('bic', False) :
                folder_name=vals['bic']
            else :
                folder_name=self.bic
            dirpath=self.env["folder.path.setting"].get_etebac3_folder()
            bank_folder=os.path.join(dirpath,folder_name)
            loaded_path=os.path.join(bank_folder, 'loaded')
            print bank_folder
            if not os.path.exists(bank_folder):
                os.makedirs(bank_folder)
                os.chmod(bank_folder,0777)
                os.makedirs(loaded_path)
                os.chmod(loaded_path,0777)
        res = super(res_bank, self).write( vals)
        return res

    @api.model
    def _load_etebac3(self):
        etebac_file_obj=self.env['etebac.file']
        dirpath=self.env["folder.path.setting"].get_etebac3_folder(True)
        if dirpath :
            bank_ids=self.search([('etebac3_file','=',True),('bic','!=',False)])
            for bank in bank_ids :
                journal_id=self.env["account.journal"].search([('bank_id',"=",bank.id),('type','=','bank')])
                bank_folder= os.path.join(dirpath, bank.bic)
                #print bank_folder
                loaded_path=os.path.join(bank_folder, 'loaded')
                if not os.path.exists(loaded_path):
                        os.makedirs(loaded_path)
                        os.chmod(loaded_path,0777)
                        #print loaded_path
                if os.path.exists(bank_folder):
                    for filename in sorted(glob.glob(os.path.join(bank_folder, '*.txt'))):
                        filepath=os.path.join(dirpath, filename)
                        name=os.path.basename(filepath)
                        self.env["positional.file"]._load_positional_file(filepath,journal_id.id,bank.id)
                        etebac_file_id=etebac_file_obj.search([('name','=',name),('state','=','loaded')])
                        if etebac_file_id :
                            new_filepath=loaded_path+'/'+name
                            os.rename(filepath, new_filepath)
                            self._cr.commit()

                else :
                     code='exchange_folder_error'
                     output="Il n'existe pas un dossier des échanges ETEBAC3 pour la banque %s dans le serveur"%(bank.name)
                     type="exchange"
                     self.env['report.exception'].set_exception(code,output)

res_bank()
