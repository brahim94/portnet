# -*- encoding: utf-8 -*-
from openerp import models, fields,  api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import psycopg2
import sys
import os
import pwd

class op_store_db_settings(models.Model):

    _name = 'op.store.db.settings'

    server=fields.Char(string="IP Serveur",required=True)
    port=fields.Char(string="Port",required=True)
    dbname=fields.Char(string="Database",required=True)
    user=fields.Char(string="Utilisateur",required=True)
    password=fields.Char(string="Mot de passe",required=False)
    is_db_store=fields.Boolean(string="Lignes de facturations ?")
    period_id=fields.Many2one(comodel_name="account.period", string="Prochaine facturation",required=True)
    state = fields.Selection(string="Statut", selection=[('draft', 'Brouillon'), ('confirmed', 'Validé')], required=False, default='draft' )

    @api.multi
    def get_cursor_database(self,server,port,dbname,user,password,cron=False) :
        try :
            conn_string ='host=%s port=%s dbname=%s user=%s password=%s'%(server,port,dbname,user,password)
            dbcon = psycopg2.connect(conn_string)
            dbcr = dbcon.cursor()
            return dbcr
        except Exception, ex:
             raise except_orm("La connexion à la base de stockage échouée","Veuillez contacter votre Administrateur")

    @api.constrains('is_db_store')
    def _check_db_store(self):
      res=self.search( [('is_db_store','=',True)] )
      if len(res) > 1:
        raise Warning("IL faut avoir une seule base de stockage")

    @api.multi
    def check_connection(self):
        try :
            conn_string ='host=%s port=%s dbname=%s user=%s password=%s'%(self.server,self.port,self.dbname,self.user,self.password)
            dbcon = psycopg2.connect(conn_string)
            dbcr = dbcon.cursor()
            """sql="select count(id) from res_partner"
            dbcr.execute(sql)
            result = map(lambda x: x[0], dbcr.fetchall())
            count=len(result)
            print "couuuuuuuuuuuuuuuuuuunt",count,result"""
        except :
            # Get the most recent exception
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            # Exit the script and print an error telling what happened.
            raise except_orm("Connexion échouée!","%s" % (exceptionValue))

        raise Warning("Connexion réussite")
    @api.one

    def set_confirmed(self):
        self.state = 'confirmed'

    @api.one
    def set_draft(self):
        self.state = 'draft'

op_store_db_settings()



class folder_path_setting(models.Model):

    _name = 'folder.path.setting'

    exchange_folder=fields.Char(string="Dossier des échanges",required=True,help="Chemin du dossier qui contient les échanges avec le systéme Poertnet")
    state=fields.Selection([('draft','Brouillon'),("confirmed","Confirmé")],string="Statu",default='draft')
    invoices_folder=fields.Char(string="Dépot Factures",required=False,help="Chemin du dossier les factures à déposer")

    @api.multi
    def unlink(self):
        if self.state=='confirmed':
             raise Warning("Vous ne pouvez pas supprimé un dossier confimé")

    @api.constrains('state')
    def _check_exchange_folder(self):
      res=self.search( [('state','=','confirmed')] )
      if len(res) > 1:
        raise Warning("Un dossier des échanges SI Portnet est déjà configuré")



    @api.multi
    def action_confirm(self):
        directory=self.exchange_folder
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chmod(directory,0777)
        invoices_folder=directory+"/"+self.invoices_folder
        if not os.path.exists(invoices_folder):
                os.makedirs(invoices_folder)
                os.chmod(invoices_folder,0777)
        self.state='confirmed'

    @api.multi
    def action_reset_to_draft(self):
        self.state='draft'

    @api.multi
    def get_invoices_folder(self,cron=False):
        exchange_folder_id=self.search([('state','=','confirmed')])
        if exchange_folder_id :
                exchange_folder=exchange_folder_id.exchange_folder
                dirpath=exchange_folder+"/"+exchange_folder_id.invoices_folder
                if not os.path.exists(exchange_folder) or  not os.path.exists(dirpath) :
                    output="Il n'existe pas un dossier pour le dépôt des factures"
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


folder_path_setting()

