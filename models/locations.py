# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, tools, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, pycompat
from odoo.addons import decimal_precision as dp


class Location(models.Model):
    _name = 'lb.location'
    _rec_name = 'contrat'

    contrat = fields.Char(string="Nom du Contrat")

    # champs---Information BIen"
    bien_loue = fields.Many2one('product.template', string="Bien Loué", required=True)
    #state qui es lié au bien
    etat_bien = fields.Selection([
        ('draft', 'New'),
        ('confirm', 'Ce Bien est deja en location'),
        ('ferme', 'contrat achevé pour Ce Bien'),
    ], string='STatut du bien choisi:', related='bien_loue.state', compute='get_contrat')



    bailleur = fields.Many2one(related='bien_loue.bailleur_id', string="Bailleur")
    type_bien = fields.Many2one(related='bien_loue.type_id', string="Type Bien")

    prixlocation_id = fields.Float(string="Prix de la location (hors charges en fcfa)",
                                   related='bien_loue.list_price', default=0.0)
    utilisation = fields.Selection([('utilisation1', 'Utilisation principale du locataire'),
                                    ('utilisation2', 'Utilisation secondaire du locataire'),
                                    ('utilisation3', 'Utilisation professionnelle')], string="Utilisation")

    # champs----locataire
    locataires = fields.Many2one('res.partner', ondelete='cascade', string="Locataire")
    mobile = fields.Char(string="N° Tel Locataire", related='locataires.phone')
    adresse_locataire = fields.Char(string="Adresse 1locataire",
                                    related='locataires.street')
    cin_ou_passeport = fields.Char(string="CIN ou passeport n°",
                                   related='locataires.num_piece_identite')

    # champs----Montant Déposé
    caution = fields.Float(string="caution déposé")
    date_depot = fields.Date(string="Date depot caution")

    depot_retourne = fields.Boolean('depot_retourne')
    maintenance = fields.Float(string="coût maintenance", default=0.0)
    date_returne = fields.Date(string="Date caution retouné")
    caution_returne = fields.Float(string="Caution Returné", default=0.0, compute='_cautionreturne')

    @api.multi
    def _cautionreturne(self):
        if self.search([('depot_retourne', '=', True)]):
            self.caution_returne = self.caution - self.maintenance
        else:
            self.caution_returne = 0.0

    # champs---information Contrat
    # validations de la date de debut et d'expiration
    date_debut = fields.Date(string="Date Début")
    date_expiration = fields.Date(string="Date D'expiration")

    date_quittancement = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'),
         ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'),
         ('18', '18'), ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'), ('25', '25'),
         ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'), ('30', '30'), ('31', '31')],
        string="Date de quittancement", help="La date selon laquelle vos quittances seraient datées")
    # duré payement
    paiement = fields.Selection([('mensuel', 'Mensuel'), ('bimestriel', 'Bimestriel'), ('trimestriel', 'Trimestriel'),
                                 ('semestriel', 'Semestriel'), ('annuel', 'Annuel'), ('forfaitaire', 'Forfaitaire')],
                                string="Durée Paiements", required=True)

    #
    loyer_sans_charges = fields.Float(string="Prix de la location en fcfa", related='bien_loue.list_price', default=0.0,
                                      digits=dp.get_precision('Loyer hors charges'), required=True)
    frais_retard = fields.Float(string='Frais de retard (%)', default=0.0,
                                digits=dp.get_precision('Frais de retard (%)'))
    autre_paiement = fields.Float(string='Autre Paiements', digits=dp.get_precision('Autre Paiements'))
    description_autre_paiement = fields.Text(string="Autre Paiements : Description")
    enregistrement_paiement = fields.One2many('lb.paiement', 'paiement_id', string="Paiements")
    condition_particuliere = fields.Text(string="Conditions")
    reste_a_payer = fields.Float(string="Reste à payer", default=0.0, digits=dp.get_precision('Reste à Payer'))
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('lb.location'),
                                 index=1)
    currency_id = fields.Many2one('res.currency', 'Currency', compute='_compute_currency_id')
    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Documents")
    locataire_a_jour = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string="Le locataire est-il à jour ?")



    @api.multi
    def print_report(self):
        return self.env.ref('location_biens.contrat_card').report_action(self)

    # états/barre LOCATION
    state = fields.Selection([
        ('draft', 'Disponible'),
        ('confirm', 'En Location'),
        ('ferme', 'Bien Disponible'),
    ], string='Status', readonly=True, default='confirm')

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'
            self.depot_retourne = False

    def action_done(self):
        for rec in self:
            rec.state = 'ferme'
            self.depot_retourne = True

    def action_cancel(self):
        for rec in self:
            rec.state = 'draft'
            self.depot_retourne = False

            # Calcul du loyer

            # Statut Location


    @api.multi
    def _compute_currency_id(self):
        try:
            main_company = self.sudo().env.ref('base.main_company')
        except ValueError:
            main_company = self.env['res.company'].sudo().search([], limit=1, order="id")
        for template in self:
            template.currency_id = template.company_id.sudo().currency_id.id or main_company.currency_id.id

            # Contrat attaché

    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for bien in self:
            bien.doc_count = Attachment.search_count([('res_model', '=', 'lb.location'), ('res_id', '=', bien.id)])

    @api.multi
    def attachment_tree_view(self):
        self.ensure_one()
        domain = [('res_model', '=', 'lb.location'), ('res_id', 'in', self.ids)]
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Cliquez sur Créer (et non importer) pour ajouter vos contrats de location</p><p>
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    @api.constrains('date_debut', 'date_expiration')
    def _check_debut_date_expiration(self):
        for r in self:
            if r.date_debut > r.date_expiration:
                raise exceptions.ValidationError("La fin du bail doit être supérieur au début du bail")



    @api.constrains('bien_loue')
    def _check_something(self):
            if (self.etat_bien ,'==' ,'confirm'):
                raise ValidationError("ce bien est en location: %s" % self.bien_loue)


class Paiement(models.Model):
    _name = 'lb.paiement'
    _rec_name = 'paiement_id'

    paiement_id = fields.Many2one('lb.location', string="Location")
    locataire_id = fields.Many2one(related='paiement_id.locataires', string="Locataire")
    loyer_sans_charges = fields.Float(related='paiement_id.loyer_sans_charges', string="Loyer charges comprises")
    fin_bail_id = fields.Date(related='paiement_id.date_expiration', string="Date Expiration")
    date_paiement = fields.Date(string="Date de Paiement", required=True)
    periode_paye_debut = fields.Date(string="Période Payée : Début", required=True)
    periode_paye_fin = fields.Date(string="Période Payée : Fin", required=True)
    montant_paye = fields.Float(string="Montant Payé", default=0.0, digits=dp.get_precision('Montant Payé'),
                                required=True)
    commentaire_paiement = fields.Text(string="Commentaire")
    objet_paiement = fields.Selection([('avance', 'Avance'), ('loyer', 'Loyer du mois'), ('pénalité', 'Pénalités'),
                                       ('autre paiements', 'Autres Paiements')], string="Objet du Paiement")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('lb.location'),
                                 index=1)
    currency_id = fields.Many2one('res.currency', 'Currency', compute='_compute_currency_id')

    # Calcul de la devise
    @api.multi
    def _compute_currency_id(self):
        try:
            main_company = self.sudo().env.ref('base.main_company')
        except ValueError:
            main_company = self.env['res.company'].sudo().search([], limit=1, order="id")
        for template in self:
            template.currency_id = template.company_id.sudo().currency_id.id or main_company.currency_id.id

