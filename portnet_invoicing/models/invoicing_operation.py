# -*- encoding: utf-8 -*-
from openerp import models, fields,  api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime
import time
class invoicing_operation(models.Model):
    _name = 'invoicing.operation'

    period_id = fields.Many2one(comodel_name="account.period", string="Période", required=True)
    invoice_ids = fields.One2many(comodel_name="account.invoice", inverse_name="invoicing_op_id", string="Factures")
    state = fields.Selection(string="Etat", selection=[('open', 'En cours'), ('done', 'Terminé')],default = 'open')


    _sql_constraints = [
        ("unique_period","UNIQUE(period_id)","La période doît être unique"),
    ]



    @api.model
    def _generate_all_invoices(self):
        databse_id=self.env['op.store.db.settings'].search([('state','=','confirmed')])
        if not databse_id :
            raise except_orm (_("Configuration Base Stockage "),
                                      _("Pas de base confirmée trouvée"))
            self.env['report.exception'].set_exception(code,output)
        dbcr=self.env['op.store.db.settings'].get_cursor_database(databse_id.server,databse_id.port,databse_id.dbname,databse_id.user,databse_id.password)
        partner_ids=self.env["res.partner"].search([('customer','=',True),('is_company','=',True),('categ_id.op_type_ids','!=',[])])
        period_id=self.period_id
        #Création de l'entité de facturation des opérations
        invoicing_op_id = False
        if period_id:
            existing_period = self.env['invoicing.operation'].search([('period_id','=',period_id.id)])
            if not existing_period:
                invoicing_op_id = self.env['invoicing.operation'].create({'period_id':period_id.id})
            else:
                invoicing_op_id = existing_period[0]
        #Création de l'entité de facturation des opérations
        for partner in partner_ids :
            self.env["customer.invoicing.wizard"]._cron_action_confirm(dbcr,partner,period_id,invoicing_op_id.id)
        dbcr.execute("COMMIT")
        for inv in self.invoice_ids:
            if inv.state == 'draft':
                self.state = 'open'
                break

    @api.one
    def unlink_draft_invoices(self):
        for inv in self.invoice_ids:
            if inv.state == 'draft':
                inv.unlink()

    @api.one
    def generate_invoices(self):
        self.unlink_draft_invoices()
        self._generate_all_invoices()

    @api.one
    def set_to_open(self):
        self.state= 'open'

    @api.one
    def set_to_done(self):
        for inv in self.invoice_ids:
            if inv.state == 'draft':
                raise except_orm (_("Facturation opérations "),
                                      _("Toutes les factures doivent être validées"))
        self.state= 'done'

    # @api.one
    # @api.depends('invoice_ids','period_id')
    # def _set_state(self):
    #     if self.period_id:
    #        count= 0
    #        if not self.invoice_ids:
    #            return "draft"
    #        else:
    #             for inv in self.invoice_ids:
    #                 if inv.state == 'open':count+=1
    #             if count == len(self.invoice_ids):
    #                 return "done"






invoicing_operation()