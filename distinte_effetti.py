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

class EffettiHeader(osv.osv):
    _name = "effetti"
    _description = "Effetti"
    
    def _importo_effetto(self, cr, uid, ids, field_name, arg, context=None):
     res = {}
     #
     for effetto in self.browse(cr, uid, ids, context=context):
         res[effetto.id] = { 'importo_effetto': 0}
         val = 0
         for line in effetto.righe_scadenze:
              val += line.importo_scadenza
         val += effetto.bolli
         res[effetto.id]['importo_effetto'] = val
     return res
    
    
    
    _columns = {
                'name': fields.char('Numero Effetto', size=64, required=True, readonly=False, select=True),
                'data_scadenza':fields.date('Data Scadenza', required=True, readonly=False, select=True),
                'cliente_id':fields.many2one('res.partner', 'Cliente', required=True),
                'banca_patner':fields.many2one('res.bank', 'Banca Cliente ', required=False, help="Banca del partner "),
                'contabilizzato':fields.boolean('Flag Contabilizzato'),
                'distinta': fields.char('Numero Distinta', size=64, required=False, readonly=False, select=True),
                'bolli':fields.float('Bolli', digits=(12, 2)),
                'note':fields.char('Note Effetto', size=80, required=True, readonly=False, select=True),
                'importo_effetto':fields.function(_importo_effetto, method=True, digits_compute=dp.get_precision('Account'), string='Importo Effetto', store=True, multi='sums'),
                'righe_scadenze':fields.one2many('effetti.scadenze', 'name', 'Scadenze'),
                                
                }
    
    
    _defaults = {
                 'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'effetti'),
                
                 }

    
    def unlink(self, cr, uid, ids, context=None):
       # controlla che l'effetto non sia in una distinta altrimenti lancia una raise
        #import pdb;pdb.set_trace()
        if context is None:
            context = {}
            """Pulisce il campo distinta presente sugli effetti """
          
        if ids: 
                for effetto in self.browse(cr,uid,ids):
                    if effetto.distinta:
                         raise osv.except_osv(_('ERRORE !'), _('Effetto  ' + effetto.name+ ' Presente in Distinta '+ effetto.distinta))
                    else:
                         for scade in effetto.righe_scadenze:
                             self.pool.get('effetti.scadenze').unlink(cr,uid,[scade.id])
                             
                result = super(EffettiHeader, self).unlink(cr, uid, ids, context=context)
        return   result

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
      # import pdb;pdb.set_trace()
      if not part:
            return {'value': {}}
      part = self.pool.get('res.partner').browse(cr, uid, part)
      if part.bank_ids:
            banca_cliente = part.bank_ids[0].bank.id
      else:
            banca_cliente = False
      val = {
               'banca_patner':banca_cliente,
               }
    
      return {'value': val}

EffettiHeader()


class EffettiScadenze(osv.osv):
    _name = "effetti.scadenze"
    _description = "Effetti dettaglio scadenze fatture"
    _columns = {
                'name': fields.many2one('effetti', 'Effetto di appartenenza', required=True, ondelete='cascade', select=True, readonly=True),
                        
                'scadenza_id':fields.many2one('fiscaldoc.scadenze', 'Scadenza', required=False, help="Aggancia Scadenza "),
                'numero_doc':fields.char('Numero Documento', size=30, required=True),
                'importo_scadenza':fields.float('Importo Scadenza', digits_compute=dp.get_precision('Account'), required=True),
                'data_documento':fields.date('Data Documento', required=True, readonly=False),
                'totale_documento':fields.float('Totale Documento', digits_compute=dp.get_precision('Account')),
                'pagamento':fields.many2one('account.payment.term', 'Pagamento', required=True),
                }

    def unlink(self, cr, uid, ids, context=None):
        #import pdb;pdb.set_trace()
        if context is None:
            context = {}
        """Pulisce il campo distinta presente sugli effetti """ 
        # va a togliere l'id dalla scadenza che lo ha generato per rigenerarlo
        for scadeff in self.browse(cr, uid, ids):                  
         if  scadeff.scadenza_id :
            ok = self.pool.get('fiscaldoc.scadenze').write(cr, uid, [scadeff.scadenza_id.id], {'effetto_scadenza_id':None})
            
        return super(EffettiScadenze, self).unlink(cr, uid, ids, context=context)    

EffettiScadenze()

class DistinteEffettiHeader(osv.osv):
    _name = "distinte.effetti"
    _description = "Distinte Effetti"
    
  

    def _totale_distinta(self, cr, uid, ids, field_name, arg, context=None):
     res = {}
     for distinta in self.browse(cr, uid, ids, context=context):
         res[distinta.id] = {'totale_distinta': 0}
         val = 0
         for line in distinta.righe_effetti:
              val += line.importo_effetto
         res[distinta.id]['totale_distinta'] = val
     return res
    
    _columns = {
                
                'company_partner_id':fields.integer('partner_id', required=True),
                'name': fields.char('Numero Distinta', size=64, required=True, readonly=False, select=True),
                'data_distinta': fields.date('Data Distinta', required=True, readonly=False, select=True),
                'banca_pres':fields.many2one('res.partner.bank', 'Banca di Presentazione', required=True, help="Banca del Azienda "),
                'note':fields.char('Note', size=128, required=True, readonly=False),
                'st_anag_compl':fields.boolean('Stampa Anagrafica Completa'),
                'data_presentazione':fields.date('Data di Presentazione della Distinta', required=True, readonly=False, select=True),
                'righe_effetti':fields.one2many('distinte.effetti.righe', 'name', 'Effetti'),
                'totale_distinta':fields.function(_totale_distinta, method=True, digits_compute=dp.get_precision('Account'), string='Totale Distinta', store=True, multi='sums'),
                'company_id': fields.many2one('res.company', 'Azienda', required=True, help=" Azienda "),
                'company_partner_id':fields.related('company_id', 'partner_id', type='integer', relation='res.partner', string='Codice Azienda Id', store=True, readonly=True),
                }
    
    def _get_partner(self, cr, uid, context=None):
            Partner_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.partner_id.id,
            #import pdb;pdb.set_trace()
            return Partner_id[0]

    _defaults = {
                 'company_partner_id':_get_partner,
                 'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'distinte.effetti'),
                 'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
                 }

    def create(self, cr, uid, vals, context=None):
        #import pdb;pdb.set_trace()
        result =  super(DistinteEffettiHeader, self).create(cr, uid, vals, context=context)
        if result:
            distinta = self.browse(cr,uid,result)
            for rig_ef in distinta.righe_effetti:
                if rig_ef.effetto_id.id:
                    ok = self.pool.get('effetti').write(cr,uid,[rig_ef.effetto_id.id],{'distinta':distinta.name})
                
        return result
        
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Pulisce il campo distinta presente sugli effetti """ 
        for distinta in self.browse(cr, uid, ids):                  
         for rec in distinta.righe_effetti:
            ok = self.pool.get('effetti').write(cr, uid, [rec.effetto_id.id], {'distinta':None})
            
        return super(DistinteEffettiHeader, self).unlink(cr, uid, ids, context=context)    
DistinteEffettiHeader()



class DistinteEffettiRighe(osv.osv):
    _name = "distinte.effetti.righe"
    _description = "Distinte Effetti"
    
    _columns = {
                'name': fields.many2one('distinte.effetti', 'Numero Distinta', required=True, ondelete='cascade', select=True, readonly=True),
                'effetto_id':fields.many2one('effetti', 'Effetto/Riba', required=True, help="Aggancia Scadenza "),
                'scadenza_effetto':fields.related('effetto_id', 'data_scadenza', type='date', relation='effetti', string='Scadenza', store=True, readonly=True),
                'cliente':fields.related('effetto_id', 'cliente_id', type='many2one', relation='res.partner', string='Cliente', store=True, readonly=True),
                'banca_patner':fields.related('effetto_id', 'banca_patner', type='many2one', relation='res.bank', string='Banca', store=True, readonly=True),
                'importo_effetto':fields.related('effetto_id', 'importo_effetto', type='float', relation='effetti', string='Importo Scadenza',digits_compute=dp.get_precision('Account'), store=True, readonly=True),
                }
    
    def unlink(self, cr, uid, ids, context=None):
        #import pdb;pdb.set_trace() 
        if context is None:
            context = {}
        """Pulisce il campo distinta presente sugli effetti """                
        for rec in self.browse(cr, uid, ids):
            ok = self.pool.get('effetti').write(cr, uid, [rec.effetto_id.id], {'distinta':None})
        return super(DistinteEffettiRighe, self).unlink(cr, uid, ids, context=context)    
    
    
DistinteEffettiRighe()


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {         
                'raggruppa_riba': fields.boolean('Raggruppa Effetti', help="Se Attivo Crea una sola Ri.Ba. per + scadenze con la stessa data e la stessa banca del partner "),
                
                }
res_partner()


class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'     
    _columns = {
                'codice_sia':fields.char('Codice SIA', size=5),
               }       

res_partner_bank()


class FiscalDocScadenze(osv.osv):
    _inherit = 'fiscaldoc.scadenze'     
    _columns = {
                'effetto_scadenza_id':fields.many2one('effetti.scadenze', 'Riga Scadenza Effetto', required=False, help="Aggancia la Riga Scadenza Dell'Effetto "),
                'generato_effetto':fields.boolean('Effetto Generato', required=False) , 
                               }       

FiscalDocScadenze()
