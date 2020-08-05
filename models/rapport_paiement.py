from odoo import models, fields, api, tools, exceptions, _
from datetime import datetime, timedelta

# Vente/Quittance
class Quittance(models.Model):
    _inherit = 'sale.order'  #

    bien_loue = fields.Many2many('product.template', ondelete='cascade', string="Bien Loué", required=True)
    bailleur_id = fields.Many2one(related='bien_loue.bailleur_id', ondelete='cascade', string="Bailleur")

    list_price = fields.Float(related='bien_loue.list_price', ondelete='cascade', string="montant")
    total = fields.Float(related='bien_loue.list_price', ondelete='cascade', string="Total")

    periode_debut = fields.Date(string="Période Payée Début")
    periode_fin = fields.Date(string="Période Payée Fin")

class order_line(models.Model):
    _inherit = 'sale.order.line'

    periode_fin =  fields.Date(string='Date payement',default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

class order(models.Model):
    _inherit = 'account.invoice.line'

    date_payement =  fields.Date(string='Date payement', required=True,default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))




