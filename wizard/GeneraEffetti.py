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


class importa_effetti(osv.osv_memory):
    _name = 'importa.effetti'
    _description = 'Importa gli effetti dai documenti di vendita'
    _columns = {
                    'a_data_doc':fields.date('Fino a Data Documento', required=True, readonly=False, select=True),
                }

    
    def importa(self, cr, uid, ids, context=None):  
         
        FinoaData = self.browse(cr, uid, ids)[0].a_data_doc
        Scadobj = self.pool.get('fiscaldoc.scadenze')
        FatObj = self.pool.get('fiscaldoc.header')
        #import pdb;pdb.set_trace() 
        filtro1 = [('tipo_documento', 'in', ('FA','FI','FD'))]
        idsTipoDoc = self.pool.get('fiscaldoc.causalidoc').search(cr, uid, filtro1)
        idsTipoDoc = tuple(idsTipoDoc)
        filtro = [('data_documento', '<=', FinoaData), ('tipo_doc', 'in', idsTipoDoc)]
        idsFat = tuple(FatObj.search(cr, uid, filtro)) # PRENDE TUTTI I DOCUMENTI FINO ALLA DATA INTERESSATA ghfg 
        filtro = [('name', 'in', idsFat), ('effetto_scadenza_id', '=', ''),('tipo_scadenza','=','RB'),('generato_effetto','=',False) ]
        idsScad = Scadobj.search(cr, uid, filtro)
        ids_effetti = []
        if idsScad:
            for scad_id in idsScad:
                Scadenzabrw = Scadobj.browse(cr, uid, [scad_id])[0]
                if  not Scadenzabrw.name.partner_id.raggruppa_riba: # se il partner raggruppa gli effetti ragiona diversamente
                    NumEff = self.pool.get('ir.sequence').get(cr, uid, 'effetti')
                    if Scadenzabrw.name.banca_patner.id:
                        TestaEffetto = {
                                    'name':NumEff,
                                    'data_scadenza':Scadenzabrw.data_scadenza,
                                    'cliente_id':Scadenzabrw.name.partner_id.id,
                                    'banca_patner':Scadenzabrw.name.banca_patner.id,
                                    'note':'Doc.N ' + str(Scadenzabrw.name.numdoc) + 'Del ' + Scadenzabrw.name.data_documento,
                                    'importo_effetto':arrot(cr,uid,Scadenzabrw.importo_scadenza,dp.get_precision('Account')),
                                    }
                        idHeadEffetto = self.pool.get('effetti').create(cr, uid, TestaEffetto)
                        ids_effetti.append(idHeadEffetto)
                        RigaEffetto = {
                                 'name':idHeadEffetto,
                                 'scadenza_id':Scadenzabrw.id,
                                 'numero_doc':Scadenzabrw.name.name,
                                 'importo_scadenza':Scadenzabrw.importo_scadenza,
                                 'data_documento':Scadenzabrw.name.data_documento,
                                 'totale_documento':arrot(cr,uid,Scadenzabrw.name.totale_documento,dp.get_precision('Account')),
                                 'pagamento':Scadenzabrw.name.pagamento_id.id,
                                 }
                        idRigaScadEff = self.pool.get('effetti.scadenze').create(cr, uid, RigaEffetto)   
                        ok = self.pool.get('effetti').write(cr, uid, idHeadEffetto, TestaEffetto)
                        for scad_eff in self.pool.get('effetti').browse(cr,uid,idHeadEffetto).righe_scadenze:
                            ok = Scadobj.write(cr,uid,scad_eff.scadenza_id.id,{'effetto_scadenza_id':scad_eff.id,'generato_effetto':True})
                    else:
                        raise osv.except_osv(_('ERRORE !'), _('Banca Assente sul documento ' + Scadenzabrw.name.name))
                    
                else:
                    # TO DO deve raggruppare l'effetto su + scadenze
                    filtro = [('data_scadenza', '', Scadenzabrw.data_scadenza), ('cliente_id', '', 'isnull')]
                    pass 
                ''' Verifica che non esista già un effetto non presentato con la stessa scadenza 
                se non  esiste crea l'effetto altrimenti aggiunge solo la scadenza e ne ricaolcola il totale effetto  '''
            pass
        else:
            raise osv.except_osv(_('ERRORE !'), _('NON SONO STATI TROVATI EFFETTI DA IMPORTARE'))
        #return {'type': 'ir.actions.act_window_close'}    # non va bene deve aprire la finestra degli effetti
        return {
            'name': _('Effetti'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'effetti',
            'res_id':ids_effetti,
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
         }   
  
importa_effetti()    
