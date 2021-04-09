# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import operator
from lxml import etree
import pytz
import datetime
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta


class PannesTypeParameter(models.Model):
    _name = 'pannes.type.parameter'
    _description = 'Type of Pannes'

    name = fields.Char(string='Type De Panne', required=True)
    code = fields.Char(string='Code', required=True)


class TicketTypeParameter(models.Model):
    _name = 'ticket.type.parameter'
    _description = 'Type of Réclamation'

    name = fields.Char(string='Type Réclamation', required=True)
    code = fields.Char(string='Code', required=True)


class DecisionParameter(models.Model):
    _name = 'decision.parameter'
    _description = 'Decision'

    name = fields.Char(string='Decision', required=True)
    code = fields.Char(string='Code', required=True)


class ActionClientParameter(models.Model):
    _name = 'action.client.parameter'
    _description = 'Actions Client'

    name = fields.Char(string='Action Client', required=True)
    code = fields.Char(string='Code', required=True)


class ActionFournisseurParameter(models.Model):
    _name = 'action.fournisseur.parameter'
    _description = 'Actions fournisseur'

    name = fields.Char(string='Action Client', required=True)
    code = fields.Char(string='Code', required=True)


class MotifParameter(models.Model):
    _name = 'motif.parameter'
    _description = 'Motif'

    name = fields.Char(string='Motif', required=True)
    code = fields.Char(string='Code', required=True)
    ticket_type_id = fields.Many2one('ticket.type.parameter', string='Type Réclamation')


class ProcessusProcessus(models.Model):
    _name = 'processus.processus'
    _description = 'Processus'

    name = fields.Char(string='Processus', required=True)
    code = fields.Char(string='Code', required=True)
    ticket_type_id = fields.Many2one('ticket.type.parameter', string='Type Réclamation')
    motif_id = fields.Many2one('motif.parameter', string='Motif')

    conditions_ids = fields.One2many('conditions.conditions', 'processus_id', string='Conditions Line', copy=False)
    decisions_ids = fields.Many2many('decision.parameter', 'decision_processus_rel', 'decision_id', 'processus_id', string='Décisions Line', copy=False)
    actions_client_ids = fields.Many2many('action.client.parameter', 'action_client_processus_rel', 'action_client_id', 'processus_id', string='Action Client Line', copy=False)
    actions_fournisseur_ids = fields.Many2many('action.fournisseur.parameter', 'action_fournisseur_processus_rel','action_fournisseur_id', 'processus_id', string='Action Fournisseur Line', copy=False)
    notification_ids = fields.One2many('notifications.notifications', 'processus_id', string='Notification Line', copy=False)
    report_1 = fields.Boolean(string='Bon de retour')
    report_2 = fields.Boolean(string='Bon de reparation')
    report_3 = fields.Boolean(string='Bon de demarque')


class ReferenceReference(models.Model):
    _name = 'reference.reference'
    _description = 'Reference'

    name = fields.Char(string='Reference', required=True)
    code = fields.Char(string='Code', required=True)


class ArticlesParameter(models.Model):
    _name = 'articles.parameter'
    _description = 'Articles'

    name = fields.Char(string='Libelle', required=True)
    code = fields.Char(string='Code', required=True)
    code_ean = fields.Char(string='Code Caisse', required=True)
    code_rayon = fields.Many2one('product.category', string='Rayon')
    code_fam = fields.Many2one('product.category', string='Famille')
    code_sfam = fields.Many2one('product.category', string='Sous Famille')
    code_ssfam = fields.Many2one('product.category', string='Sous Sous Famille')
    fournisseur = fields.Many2one('res.partner', string='Fournisseur')
    garantie = fields.Selection([('day', 'Jours'), ('week', 'Semaines'), ('month', 'Mois'), ('year', 'Annees')], string='Type durée')
    duree = fields.Integer(string='Duree')


class ConditionsConditions(models.Model):
    _name = 'conditions.conditions'
    _description = 'Conditions Lines'

    processus_id = fields.Many2one('processus.processus', string='Processus')
    type_condition = fields.Selection([('delai', 'Delai'), ('no_repair', 'Nombre de reparations')], string='Type Conditions', default='delai')
    reference_1 = fields.Many2one('reference.reference', string='Reference1')
    reference_2 = fields.Many2one('reference.reference', string='Reference2')
    unite = fields.Selection([('hour', 'Heure'), ('day', 'Jour'), ('week', 'Semaine'), ('month', 'Mois'), ('year', 'Annee')], string='Unite')
    operator = fields.Selection([('=', '='), ('<', '<'), ('>', '>'), ('<=', '<='), ('>=', '>=')], string='Operator')
    valeur = fields.Integer(string='Valeur')


class NotificationsNotifications(models.Model):
    _name = 'notifications.notifications'
    _description = 'Notification Lines'

    processus_id = fields.Many2one('processus.processus', string='Processus')
    ticket_id = fields.Many2one('ticket.ticket', string='Réclamation')
    name = fields.Char(string='Description', required=True)
    base_type = fields.Selection([('decisions', 'Décisions'), ('action_client', 'Action Client'), ('action_fournisseur', 'Action Fournisseur')], string='Base', required=True)
    decision_id = fields.Many2one('decision.parameter', string='Decision')
    action_client_id = fields.Many2one('action.client.parameter', string='Action Client')
    fournisseur_id = fields.Many2one('action.fournisseur.parameter', string='Etat déclencheur')
    destinataire_id = fields.Selection([('sav', 'Responsible SAV'), ('fournisseur', 'Fournisseur'), ('client', 'Client'), ('prestataire', 'Prestataire')], string='Destinataire')
    notification_type = fields.Selection([('automatic', 'Automatique'), ('manual', 'Manuel')], string='Notification Type', default='automatic')
    unite = fields.Selection([('day', 'Jours'), ('week', 'Semaines'), ('month', 'Mois'), ('year', 'Annees')], string='Unite')
    valeur = fields.Integer(string='Valeur')
    notification_email_mode = fields.Boolean(string='Email')
    notification_sms_mode = fields.Boolean(string='SMS')
    email_to = fields.Many2one('mail.template', string='Email To')
    sms_to = fields.Text(string='SMS To')
    date_sent = fields.Date(string='Date envoi')
    state = fields.Selection([('new', 'New'), ('sent', 'Sent')], string='Etat', readonly=True, copy=False, index=True, track_visibility='onchange', default='new')

    @api.multi
    def action_send_email(self):
        context = dict(self.env.context or {})
        if context.get('ticket_id'):
            ticket = self.env['ticket.ticket'].browse(context['ticket_id'])
            partner = ticket._get_partner(ticket, self.destinataire_id)
            if partner:
                (self.email_to).send_mail(ticket.id,
                    force_send=True,
                    email_values={'recipient_ids': [(4, partner)]}
                )
                self.write({'state': 'sent', 'date_sent': fields.Date.today()})



class TicketTicket(models.Model):
    _name = 'ticket.ticket'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Réclamation'

    name = fields.Char(string='Nº Réclamation', required=True, copy=False, index=True, default=lambda self: _('New'))
    ticket_type_id = fields.Many2one('ticket.type.parameter', string='Type Réclamation', required=True)
    is_enable = fields.Selection([('code1', 'code1'), ('code2', 'code2')], string='Is Enable ?')
    invoice_id = fields.Many2one('factures.factures', string='Nº Facture')
    client_id = fields.Many2one('res.partner', string='Client')
    date_achat = fields.Datetime(string='Date d’achat', track_visibility='onchange')
    garantie = fields.Selection([('day', 'Jours'), ('week', 'Semaines'), ('month', 'Mois'), ('year', 'Annees')], string='Type durée')
    duree = fields.Integer(string='Duree', required=True)
    garantie_date = fields.Date(compute='_compute_garantie_date', string='Garantie Date')
    article_id = fields.Many2one('articles.parameter', string='Désignation Article', required=True)
    article_code = fields.Char(string='Code article')
    n_serie = fields.Char(string='Nº serie')
    fournisseur = fields.Many2one('res.partner', string='Fournisseur', required=True)
    prestataire = fields.Many2one('res.partner', string='Prestataire', required=True)
    motif_id = fields.Many2one('motif.parameter', string='Motif', required=True, track_visibility='onchange')
    panne_type_id = fields.Many2one('pannes.type.parameter', string='Type de panne', required=True, track_visibility='onchange')
    decision_id = fields.Many2one('decision.parameter', string='Décision', required=True, track_visibility='onchange')
    action_client_id = fields.Many2one('action.client.parameter', string='Action Client', required=True, track_visibility='onchange')
    fournisseur_id = fields.Many2one('action.fournisseur.parameter', string='Action fournisseur', required=True, track_visibility='onchange')
    date = fields.Datetime(string='Date', required=True, copy=False, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Créer par', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    remarque = fields.Text(string='Remarques')
    is_enable_motif = fields.Boolean(string='Enable Motif')
    
    # Client Fields
    client_type = fields.Selection([('perticular', 'Particulier'), ('enterprise', 'Enterprise')], string='Client Type', default='perticular')
    client_nom = fields.Char(string='Nom')
    client_representant = fields.Char(string='Representant')
    client_cin = fields.Char(string='CIN')
    client_phone = fields.Char(string='N° de telephone')
    client_email = fields.Char(string='Client Email')
    client_ice = fields.Char(string='ICE')
    client_street = fields.Char(string='Client Address 1')
    client_street2 = fields.Char(string='Client Address 2')
    client_zip = fields.Char(string='Client Code Postal')
    client_city = fields.Char(string='Client Ville')

    # Supplier Fields
    supplier_nom = fields.Char(string='Raison Sociale')
    supplier_phone = fields.Char(string='N° de telephone Standard')
    supplier_mobile = fields.Char(string='N° de telephone Mobile')
    supplier_email = fields.Char(string='Supplier Email')
    supplier_telex = fields.Char(string='Telex')
    supplier_telecopier = fields.Char(string='Telecopier')
    supplier_code = fields.Char(string='Code')
    supplier_street = fields.Char(string='Supplier Address 1')
    supplier_street2 = fields.Char(string='Supplier Address 2')
    supplier_zip = fields.Char(string='Supplier Code Postal')
    supplier_city = fields.Char(string='Supplier Ville')
    supplier_website = fields.Char(string='Website')

    report_1 = fields.Boolean(string='Bon de retour')
    report_2 = fields.Boolean(string='Bon de reparation')
    report_3 = fields.Boolean(string='Bon de demarque')

    manual_notification_count = fields.Integer(compute='_count_manual_notification', string='Notifications Count')

    suivi_ids = fields.One2many('ticket.suivi', 'ticket_id', string='Suivis')
    ticket_history_ids = fields.Many2many('ticket.ticket', 'rel_ticket_ticket', 'ticket_id', 'new_ticket_id', string='Historique réparations')
    notification_ids = fields.One2many('notifications.notifications', 'ticket_id', string='Notification Line', copy=False)
    state = fields.Selection([
        ('inprogress', 'En cours'),
        ('done', 'Clôturé'),
        ('cancel', 'Annulé'),
    ], string='Etat', readonly=True, copy=False, default='inprogress')

    date_plu_tweenty = fields.Datetime(string="Date limite", compute='_add_tweenty')

    @api.multi
    def _add_tweenty(self):
        for order in self:
            duree_mois = 20
            if self.date:
                date_start_dt = fields.Datetime.from_string(self.date)
                dt = date_start_dt + relativedelta(days=duree_mois)
                date_plu_tweenty = fields.Datetime.to_string(dt)
        order.update({'date_plu_tweenty': date_plu_tweenty})

    @api.depends('date_achat','garantie','duree')
    def _compute_garantie_date(self):
        for record in self:
            if record.date_achat and record.garantie and record.duree:
                date = record._get_new_date(record.date_achat, record.garantie, record.duree)
                record.garantie_date = fields.Date.to_string(date) if date else ''

    @api.multi
    def action_done(self):
        self.state = 'done'
        
    @api.multi
    def print_bonreparation(self):
        return self.env.ref('wt_helpdesk.action_report_helpdesk').report_action(self)
    
    @api.multi
    def print_bonderetour(self):
        return self.env.ref('wt_helpdesk.action_report_helpdesk_bonretour').report_action(self)

    @api.multi
    def print_bon_de_demarque(self):
        return self.env.ref('wt_helpdesk.action_report_helpdesk_bon_de_demarque').report_action(self)

    @api.multi
    def button_manual_notification(self):
        context = dict(self.env.context or {})
        context['ticket_id'] = self.id
        return {
            'name': _('Notifications'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'notifications.notifications',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.notification_ids.ids or False)],
            'context': context,
        }

    @api.depends('notification_ids')
    def _count_manual_notification(self):
        for record in self:
            record.manual_notification_count = len(record.notification_ids.filtered(lambda l: l.state == 'new'))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ticket.ticket') or _('New')
        return super(TicketTicket, self).create(vals)

    @api.multi
    def write(self, values):
        values.update({'is_enable_motif': False})
        return super(TicketTicket, self).write(values)

    @api.onchange('is_enable_motif')
    def onchange_enable(self):
        if self.is_enable_motif:
            result = {}
            res = self.onchange_domain_motif()
            res1 = self.onchange_motif()
            if res:
                result.setdefault('domain', {}).update(res['domain'])
            if not res and res1 != None:
                result.setdefault('domain', {}).update(res1['domain'])
            if res and res1 != None:
                result.get('domain').update(res1['domain'])
            return result

    @api.onchange('ticket_type_id')
    def onchange_ticket_type_id(self):
        if self.ticket_type_id and self.ticket_type_id.code == '1':
            self.is_enable = 'code1'
        elif self.ticket_type_id and self.ticket_type_id.code != '1':
            self.is_enable = 'code2'
        else:
            self.is_enable = False

    @api.onchange('client_id')
    def onchange_client_id(self):
        if self.client_id:
            self.client_nom = self.client_id.name
            self.client_phone = self.client_id.mobile
            self.client_email = self.client_id.email
            self.client_street = self.client_id.street
            self.client_street2 = self.client_id.street2
            self.client_zip = self.client_id.zip
            self.client_city = self.client_id.city
            self.client_cin = self.client_id.ref
        else:
            self.client_nom = ''
            self.client_phone = ''
            self.client_email = ''
            self.client_street = ''
            self.client_street2 = ''
            self.client_zip = ''
            self.client_city = ''
            self.client_cin = ''

    @api.onchange('fournisseur')
    def onchange_fournisseur_id(self):
        if self.fournisseur:
            self.prestataire = self.fournisseur.id
            self.supplier_nom = self.fournisseur.name
            self.supplier_phone = self.fournisseur.phone
            self.supplier_mobile = self.fournisseur.mobile
            self.supplier_email = self.fournisseur.email
            self.supplier_street = self.fournisseur.street
            self.supplier_street2 = self.fournisseur.street2
            self.supplier_zip = self.fournisseur.zip
            self.supplier_city = self.fournisseur.city
            self.supplier_website = self.fournisseur.website
            self.supplier_code = self.fournisseur.code_fournisseur

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id:
            self.date_achat = self.invoice_id.date
            self.article_id = self.invoice_id.article_id.id
            self.n_serie = self.invoice_id.serial_number
            self.fournisseur = self.invoice_id.article_id.fournisseur
            ticket_ids = self.env['ticket.ticket'].search([('invoice_id.name', '=', self.invoice_id.name)])
            self.ticket_history_ids = ticket_ids.ids if ticket_ids else False
        else:
            self.ticket_history_ids = False

    @api.onchange('article_id')
    def onchange_article_id(self):
        if self.article_id:
            self.garantie = self.article_id.garantie
            self.duree = self.article_id.duree
            self.article_code = self.article_id.code

    def _get_new_date(self, date_purchase, period, value):
        date = date_purchase
        if period == 'hour':
            date = date_purchase + relativedelta(hours=value, minute=0, second=0)
        elif period == 'day':
            date = date_purchase + relativedelta(days=value, hour=0, minute=0, second=0)
        elif period == 'week':
            date = date_purchase + relativedelta(weeks=value, hour=0, minute=0, second=0)
        elif period == 'month':
            date = date_purchase + relativedelta(months=value, hour=0, minute=0, second=0)
        elif period == 'year':
            date = date_purchase + relativedelta(years=value, hour=0, minute=0, second=0)
        else:
            date = date_purchase + relativedelta(hour=0, minute=0, second=0)
        return date

    def _get_motif(self, date_purchase, period, period_value, date, ticket_type_id):
        motif_lis = []
        ops = {'>': operator.gt,'<': operator.lt,'>=': operator.ge,'<=': operator.le,'=': operator.eq}
        for process_id in self.env['processus.processus'].search([('motif_id', '!=', False),('ticket_type_id', '=', ticket_type_id.id)]):
            results = []
            for line in process_id.conditions_ids:
                if line.type_condition == 'delai' and line.reference_1 and line.reference_2:
                    source_date = False
                    destination_date = False
                    warranty_date = self._get_new_date(date_purchase, period, period_value)
                    if line.reference_1.code == 'purchase_date':
                        if line.unite == 'hour':
                            source_date = date_purchase + relativedelta(minute=0, second=0)
                        else:
                            source_date = date_purchase + relativedelta(hour=0, minute=0, second=0)

                        if line.reference_2.code == 'ticket_date':
                            destination_date = self._get_new_date(date, line.unite, line.valeur)
                        elif line.reference_2.code == 'warranty_date':
                            destination_date = self._get_new_date(warranty_date, line.unite, line.valeur)
                        elif line.reference_2.code == 'today_date':
                            destination_date = self._get_new_date(fields.Datetime.today(), line.unite, line.valeur)
                        else:
                            continue
                    elif line.reference_1.code == 'ticket_date':
                        if line.unite == 'hour':
                            source_date = date + relativedelta(minute=0, second=0)
                        else:
                            source_date = date + relativedelta(hour=0, minute=0, second=0)

                        if line.reference_2.code == 'purchase_date':
                            destination_date = self._get_new_date(date_purchase, line.unite, line.valeur)
                        elif line.reference_2.code == 'warranty_date':
                            destination_date = self._get_new_date(warranty_date, line.unite, line.valeur)
                        elif line.reference_2.code == 'today_date':
                            destination_date = self._get_new_date(fields.Datetime.today(), line.unite, line.valeur)
                        else:
                            continue
                    elif line.reference_1.code == 'warranty_date':
                        if line.unite == 'hour':
                            source_date = warranty_date + relativedelta(minute=0, second=0)
                        else:
                            source_date = warranty_date + relativedelta(hour=0, minute=0, second=0)

                        if line.reference_2.code == 'purchase_date':
                            destination_date = self._get_new_date(date_purchase, line.unite, line.valeur)
                        elif line.reference_2.code == 'ticket_date':
                            destination_date = self._get_new_date(date, line.unite, line.valeur)
                        elif line.reference_2.code == 'today_date':
                            destination_date = self._get_new_date(fields.Datetime.today(), line.unite, line.valeur)
                        else:
                            continue
                    elif line.reference_1.code == 'today_date':
                        if line.unite == 'hour':
                            source_date = fields.Datetime.today() + relativedelta(minute=0, second=0)
                        else:
                            source_date = fields.Datetime.today() + relativedelta(hour=0, minute=0, second=0)

                        if line.reference_2.code == 'purchase_date':
                            destination_date = self._get_new_date(date_purchase, line.unite, line.valeur)
                        elif line.reference_2.code == 'ticket_date':
                            destination_date = self._get_new_date(date, line.unite, line.valeur)
                        elif line.reference_2.code == 'warranty_date':
                            destination_date = self._get_new_date(warranty_date, line.unite, line.valeur)
                        else:
                            continue
                    else:
                        continue
                    if source_date and destination_date and line.operator:
                        if ops[line.operator](source_date, destination_date):
                            results.append(True)
                if line.type_condition == 'no_repair':
                    ticket_ids = self.env['ticket.ticket'].search([
                        ('invoice_id.name','=',self.invoice_id.name),
                        ('article_code','=',self.article_code),
                        ('panne_type_id','=',self.panne_type_id.id),
                        ('n_serie','!=',False),
                        ('n_serie','=',self.n_serie)])
                    if line.operator and line.valeur:
                        if ops[line.operator](len(ticket_ids), line.valeur):
                            results.append(True)
            if results and len(results) == len(process_id.conditions_ids):
                motif_lis.append(process_id.motif_id.id)
            if not results and not process_id.conditions_ids:
                motif_lis.append(process_id.motif_id.id)
        return motif_lis

    @api.onchange('date_achat', 'garantie', 'duree', 'date', 'panne_type_id', 'ticket_type_id', 'article_code', 'n_serie', 'invoice_id')
    def onchange_domain_motif(self):
        if self.date_achat and self.garantie and self.duree and self.date and self.ticket_type_id:
            # user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(self._context.get('tz') or 'UTC')
            motif_ids = self._get_motif(
                fields.Datetime.from_string(datetime.strftime(pytz.utc.localize(datetime.strptime(fields.Datetime.to_string(self.date_achat), DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),DEFAULT_SERVER_DATETIME_FORMAT)),
                self.garantie, 
                self.duree, 
                fields.Datetime.from_string(datetime.strftime(pytz.utc.localize(datetime.strptime(fields.Datetime.to_string(self.date), DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),DEFAULT_SERVER_DATETIME_FORMAT)),
                self.ticket_type_id)
            # motif_ids = self._get_motif(self.date_achat, self.garantie, self.duree, self.date, self.ticket_type_id)
            return {'domain': {'motif_id': [('id', 'in', motif_ids)]}}
        else:
            return {'domain': {'motif_id': [('id', 'in', [])]}}

    @api.onchange('motif_id')
    def onchange_motif(self):
        if self.motif_id:
            process = self.env['processus.processus'].search([('motif_id','=',self.motif_id.id)], limit=1)
            self.report_1 = process.report_1 if process else False
            self.report_2 = process.report_2 if process else False
            self.report_3 = process.report_3 if process else False
            return {'domain':{
                        'decision_id': [('id', 'in', process.decisions_ids.ids if process.decisions_ids else [])],
                        'action_client_id': [('id', 'in', process.actions_client_ids.ids if process.actions_client_ids else [])],
                        'fournisseur_id': [('id', 'in', process.actions_fournisseur_ids.ids if process.actions_fournisseur_ids else [])]}}

    def _get_date(self, period, value):
        date = fields.Date.today()
        if period == 'day':
            date = date - relativedelta(days=value, hour=0, minute=0, second=0)
        elif period == 'week':
            date = date - relativedelta(weeks=value, hour=0, minute=0, second=0)
        elif period == 'month':
            date = date - relativedelta(months=value, hour=0, minute=0, second=0)
        elif period == 'year':
            date = date - relativedelta(years=value, hour=0, minute=0, second=0)
        else:
            date = date
        return date
    
    def _get_tickets(self, type, decision_id, action_client_id, fournisseur_id, date):
        ticket_ids = []
        Ticket = self.env['ticket.ticket']
        if type == 'decisions' and decision_id:
            tickets = Ticket.search([('decision_id','=',decision_id.id)])
            if tickets:
                ticket_ids = tickets.filtered(lambda t: fields.Date.to_string(t.date) == fields.Date.to_string(date))
        if type == 'action_client' and action_client_id:
            tickets = Ticket.search([('action_client_id','=',action_client_id.id)])
            if tickets:
                ticket_ids = tickets.filtered(lambda t: fields.Date.to_string(t.date) == fields.Date.to_string(date))
        if type == 'action_fournisseur' and fournisseur_id:
            tickets = Ticket.search([('fournisseur_id','=',fournisseur_id.id)])
            if tickets:
                ticket_ids = tickets.filtered(lambda t: fields.Date.to_string(t.date) == fields.Date.to_string(date))
        return ticket_ids

    def _get_partner(self, ticket, destination):
        partner = False
        if destination and destination == 'sav':
            partner = ticket.user_id.partner_id.id
        if destination and destination == 'fournisseur':
            partner = ticket.fournisseur.id
        if destination and destination == 'client':
            partner = ticket.client_id.id
        if destination and destination == 'prestataire':
            partner = ticket.prestataire.id
        return partner

    @api.model
    def send_ticket_notification(self):
        for notification in self.env['notifications.notifications'].search([('ticket_id','=',False), ('processus_id','!=',False)]):
            if notification.notification_email_mode:
                date = self._get_date(notification.unite, notification.valeur)
                for ticket in self._get_tickets(notification.base_type, notification.decision_id, notification.action_client_id, notification.fournisseur_id, date):
                    partner = self._get_partner(ticket, notification.destinataire_id)
                    if partner:
                        if notification.notification_type == 'automatic':
                            new_notification_id = notification.copy(default={'ticket_id':ticket.id, 'processus_id':False, 'state': 'new'})
                            (new_notification_id.email_to).send_mail(ticket.id,
                                force_send=True,
                                email_values={'recipient_ids': [(4, partner)]}
                            )
                            new_notification_id.write({'state': 'sent', 'date_sent': fields.Date.today()})
                        if notification.notification_type == 'manual':
                            new_notification_id = notification.copy(default={'ticket_id':ticket.id, 'processus_id':False, 'state': 'new'})


class TicketSuivi(models.Model):
    _name = 'ticket.suivi'
    _description = 'Réclamation Suivi'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    
    ticket_id = fields.Many2one('ticket.ticket', string='Réclamation', required=True) 
    name = fields.Integer(string='N° Séquence', required=True)
    desc = fields.Char(string='Description', required=True)
    date = fields.Datetime(string='Date d\'ouverture',required=True)
    date_fin = fields.Datetime(string='Date de clôture')
    email = fields.Boolean(string='Envoyer E-mail?')
    sms = fields.Boolean(string='Envoyer SMS?')
    appel = fields.Boolean(string='Planifier un  Appel?')
    relance = fields.Boolean(string='Relance?')
    email_liste = fields.Char(string='Adresses e-mail')
    gsm_liste = fields.Char(string='GSM')
    duree = fields.Float(string='Durée Estimée (J)')
    duree_reel = fields.Float(string='Durée Réele (J)')
    mode = fields.Selection([
          ('Client', 'Client'),
          ('Magasin', 'Magasin'),
          ('SAV', 'SAV'),
          ('Logistique', 'Service Logistique'),
          ('Fournisseur', 'Fournisseur'),
          ('Finannce et facturation', 'Finannce et facturation'),
          ('Commercial', 'Service Commercial'),
          ('Stock', 'Service Stock'),
          ('Achat', 'Service Achat'),
          ('centre appel', 'Centre d\'appel'),
          ('Direction', 'Direction'),
        ], string='Acteur', required=True)
    state = fields.Selection([('brouillon', 'Nouveau'),('encours', 'En cours'), ('Termine', 'Terminé'),('Annule', 'Annulé'), ], string='Etat', default="brouillon")
    image1 = fields.Binary("Image 1", attachment=True)
    image2 = fields.Binary("Image 2", attachment=True)
    image3 = fields.Binary("Image 3", attachment=True)
    image4 = fields.Binary("Image 4", attachment=True)

    remarque = fields.Text(string='Remarques')
    model_id = fields.Many2one('mail.template', string='Modéle e-mail')
    model_relance_id = fields.Many2one('mail.template', string='Modéle e-mail de Relance') 
    sms_model = fields.Text(string='Modéle SMS')
    duree = fields.Float(string='Durée estimée (J)')
    type = fields.Selection([
          ('Oblegatoire', 'Oblégatoire'),
          ('Optionnelle', 'Optionnelle'),], string='Type', required=True)


class FacturesFactures(models.Model):
    _name = 'factures.factures'
    _description = 'Factures'
    _order = 'name'

    name = fields.Char(string='Code')
    sequence = fields.Integer(string='Line Number', required=True)
    invoice_number = fields.Char(string='Numero de facture', required=True)
    date = fields.Datetime(string='Date d achat', required=True)
    article_id = fields.Many2one('articles.parameter', string='Article', required=False)
    article = fields.Char(string='Article', required=False)

    amount = fields.Float(string='Montant', required=True)
    serial_number = fields.Char(string='N serie')
    qty = fields.Float(string='Quantite', required=True)
    id_magas_in = fields.Char(string='ID MAGAS IN')

    @api.onchange('invoice_number', 'sequence')
    def onchange_invoice_number_sequence(self):
        if self.invoice_number and self.sequence:
            self.name = self.invoice_number + '-' + str(self.sequence)

