# -*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import decimal_precision as dp
import time
import netsvc
import pooler, tools
import math
from tools.translate import _

from osv import fields, osv

def arrot(cr,uid,valore,decimali):
    #import pdb;pdb.set_trace()
    return round(valore,decimali(cr)[1])

class gendist_effetti(osv.osv_memory):
    _name = 'gendist.effetti'
    _description = 'Genera le distinte di presentazione Effetti '
    _columns = {
                    
                    'company_partner_id':fields.integer('partner_id', required=True),
                    'banca_pres':fields.many2one('res.partner.bank', 'Banca di Presentazione ', required=True, help="Banca di Presentazione dell'azienda "),
                    'da_data_scadenza':fields.date('Da Data Scadenza', required=True, readonly=False),
                    'a_data_scadenza':fields.date('A Data Scadenza', required=True, readonly=False),
                    'data_distinta': fields.date('Data Distinta', required=True, readonly=False, select=True),
                    'st_anag_compl':fields.boolean('Stampa Anagrafica Completa'),
                    'data_presentazione':fields.date('Data di Presentazione ', required=True, readonly=False, select=True),
                    'totale_importo':fields.float('Importo Massimo Distinta', digits=(12, 2)),
                   
                    }
    
    def _get_partner(self, cr, uid, context=None):
            Partner_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.partner_id.id,
            #import pdb;pdb.set_trace()
            return Partner_id[0]
    
    _defaults = {
               'company_partner_id':_get_partner,
               'totale_importo':9999999999,
               'data_distinta':lambda * a: time.strftime('%Y-%m-%d'),
               'data_presentazione':lambda * a: time.strftime('%Y-%m-%d'),
               'da_data_scadenza':lambda * a: time.strftime('%Y-%m-%d'),
               }
    


    def generadist(self, cr, uid, ids, context=None): 
    
     Parametri = self.browse(cr, uid, ids)[0]
     cerca = [
             ('data_scadenza', '>=', Parametri.da_data_scadenza),
             ('data_scadenza', '<=', Parametri.a_data_scadenza),
             ('distinta', '=', None),
             ]
     ids_eff = self.pool.get('effetti').search(cr, uid, cerca,order='data_scadenza')
     First = True
     totale_distinta = 0
     if ids_eff:
       for effetto in self.pool.get('effetti').browse(cr, uid, ids_eff):
           if not effetto.distinta or len(effetto.distinta)==0:
               if First:
                   First = False
                   # crea l'id della distinta
                   testa_distinta = {
                                     'banca_pres':Parametri.banca_pres.id,
                                     'data_distinta':Parametri.data_distinta,
                                     'st_anag_compl':Parametri.st_anag_compl,
                                     'data_presentazione':Parametri.data_presentazione,
                                     'note':'Distinta'
                                     }
                   id_distinta = self.pool.get('distinte.effetti').create(cr, uid, testa_distinta)
               
               if totale_distinta + effetto.importo_effetto <= Parametri.totale_importo:
                   totale_distinta += arrot(cr,uid,effetto.importo_effetto,dp.get_precision('Account'))
                   riga_distinta = {
                                    'name':id_distinta,
                                    'effetto_id':effetto.id,
                                    }
                   id_riga_distinta = self.pool.get('distinte.effetti.righe').create(cr, uid, riga_distinta)
                   agg_effetto = {
                                  'distinta':self.pool.get('distinte.effetti').browse(cr, uid, [id_distinta])[0].name,
                                  }
                   #import pdb;pdb.set_trace()
                   ok = self.pool.get('effetti').write(cr, uid, [effetto.id], agg_effetto) 
       # Scrive l'importo totale della distinta  
       testa_distinta = {
                                     'totale_distinta':totale_distinta,
                          }
       ok = self.pool.get('distinte.effetti').write(cr, uid, [id_distinta], testa_distinta)
            
                
       return {
            'name': _('Distinte Effetti'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'distinte.effetti',
            'res_id':id_distinta,
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
         }      
     else:
        raise osv.except_osv(_('ERRORE !'), _('Non ci sono Effetti per questa selezione  '))   
        return {'type': 'ir.actions.act_window_close'}    # non va bene deve aprire la finestra degli effetti
    # context.update({'product_id':id_Articolo})
 

gendist_effetti()

