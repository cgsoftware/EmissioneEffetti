# -*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import decimal_precision as dp
import time
import netsvc
import pooler, tools
import math
from tools.translate import _
import base64

from osv import fields, osv


def arrot(cr,uid,valore,decimali):
    #import pdb;pdb.set_trace()
    return round(valore,decimali(cr)[1])

class GenFileRiba(osv.osv_memory):
    _name = 'gen.fileriba'
    _description = 'Genera file riba di una distinta di presentazione effetti '
    _columns = {
                    
                    'distinta_id':fields.many2one('distinte.effetti', 'Numero Distinta', required=True, ondelete='cascade', select=True, readonly=True),
                    'state': fields.selection((('choose', 'choose'), # choose accounts
                                               ('get', 'get'), # get the file
                                   )),
                    #'nomefile':fields.char('Nome del file',size=20,required = True)
                    'data': fields.binary('File', readonly=True),

                    }
    '''   def _creaFile(self, intestazione, ricevute_bancarie):
        accumulatore = self._RecordIB(intestazione[0], intestazione[3], intestazione[4], intestazione[5])
        for value in ricevute_bancarie: #estraggo le ricevute dall'array
            self._progressivo = self._progressivo + 1
            accumulatore = accumulatore + self._Record14(
                value[1], value[2], intestazione[0], intestazione[1], intestazione[2], value[8], value[9], value[11])
            accumulatore = accumulatore + self._Record20(intestazione[6], intestazione[7], intestazione[8], intestazione[9])
            accumulatore = accumulatore + self._Record30(value[3], value[4])
            accumulatore = accumulatore + self._Record40(value[5], value[6], value[7], value[10])
            accumulatore = accumulatore + self._Record50(value[12], intestazione[10])
            accumulatore = accumulatore + self._Record51(value[0])
            accumulatore = accumulatore + self._Record70()
        accumulatore = accumulatore + self._RecordEF()
        return accumulatore '''
    
    def _get_distinta(self, cr, uid, context=None):
        id_distinta = context.get('active_ids', [])
        return id_distinta[0]
    
    _defaults = {
                 'state': lambda * a: 'choose',
                 'distinta_id':_get_distinta,
                 }
    
    



    def generariba(self, cr, uid, ids, context=None): 
        
        DistintaId = self.browse(cr, uid, ids)[0].distinta_id
        CodiceSia = DistintaId.banca_pres.codice_sia
        RecBanca = DistintaId.banca_pres.bank
        AziendaRec = self.pool.get('res.partner').browse(cr, uid, [DistintaId.company_partner_id])[0]
        AddressAzi = AziendaRec.address[0]
        if DistintaId.righe_effetti:
            DatiAzienda = {}
            DatiAzienda.update({'RagAzi':AziendaRec.name.ljust(24)[:24]})
            DatiAzienda.update({'IndAzi':AddressAzi.street.ljust(24)[:24]})
            DatiAzienda.update({'LocAzi':AddressAzi.zip.ljust(5) + " " + AddressAzi.city + " " + AddressAzi.province.code})
            DatiAzienda['LocAzi'].ljust(24)[:24]
            DatiAzienda.update({'CodiceSia':CodiceSia.rjust(5, "0")[:5]})
            DatiAzienda.update({'Abi':RecBanca.codice_abi.rjust(5, "0")[:5]})
            DatiAzienda.update({'Cab':RecBanca.codice_cab.rjust(5, "0")[:5]})
            DatiAzienda.update({'NumConto':" ".ljust(12)[:12]})
            oggi = datetime.today()
            DatiAzienda.update({'DataCre':str(oggi.day).rjust(2, "0") + str(oggi.month).rjust(2, "0") +  str(oggi.year)[2:] })
            DatiAzienda.update({'OraCre':str(oggi.hour).rjust(2, "0") + str(oggi.minute).rjust(2, "0") + str(oggi.second).rjust(2, "0")})
            DatiAzienda.update({'NomeSupporto':DatiAzienda['DataCre'] + DatiAzienda['OraCre'] + DatiAzienda['CodiceSia']})
            #* --- spazio a disposizione
            w_DISPOS = "".ljust(6)
            #  --- centro applicativo (ad uso solo degli istituti bancari)
            w_CENAPP = "".ljust(5)
            NumRiba = 0
            NumeroRecord = 0
            File = """"""
            Intestazione = " IB" + DatiAzienda['CodiceSia'] + DatiAzienda['Abi'] + DatiAzienda['DataCre'] + DatiAzienda['NomeSupporto']
            Intestazione = Intestazione + w_DISPOS + "".ljust(71) + "E" + "".ljust(1) + w_CENAPP + "\r\n"
            NumeroRecord += 1
            File += Intestazione       
            TotaleEff = 0     
            for Effetto in DistintaId.righe_effetti:
                # Inizio Record 14
                NumRiba += 1 ## numero della riba sul file
                NumDis = str(NumRiba).rjust(7, "0")
                DatSca = Effetto.effetto_id.data_scadenza[8:10] + Effetto.effetto_id.data_scadenza[5:7] + Effetto.effetto_id.data_scadenza[2:4]
                Impo = arrot(cr,uid,Effetto.importo_effetto,dp.get_precision('Account'))
                ImportoEffetto = Impo 
                diff = (ImportoEffetto - int(ImportoEffetto))*100
                
                if diff < 10 :
                    #import pdb;pdb.set_trace()
                    diff = '0'+str(diff)[0]
                else: 
                    diff = str(diff)[:2]
                ImpEff = str(int(ImportoEffetto))  + diff
                TotaleEff += Effetto.importo_effetto
                ImpEff = ImpEff.rjust(13, "0")
                ClienteRec = Effetto.cliente
                abi = Effetto.banca_patner.codice_abi.rjust(5, "0")[:5]
                cab = Effetto.banca_patner.codice_cab.rjust(5, "0")[:5]                
                if ClienteRec.ref:
                    codcli = ClienteRec.ref.strip().ljust(16)[:16]
                else:
                    codcli = "".ljust(16)[:16]
                Record = " 14" + NumDis + " " * 12 + DatSca + "30000" + ImpEff + "-" + DatiAzienda['Abi'] + DatiAzienda['Cab'] + " " * 12 + abi + cab
                Record = Record + " " * 12 + DatiAzienda['CodiceSia'] + "4" + codcli + " " * 6 + "E" + "\r\n"
                NumeroRecord += 1
                File += Record
                # Inizio Record 20
                Record = " 20" + NumDis + DatiAzienda['RagAzi'] + DatiAzienda['IndAzi'] + DatiAzienda['LocAzi'] + " " * 24 + "\r\n"
                NumeroRecord += 1
                File += Record
                # Inizio Record 30
                Record = " 30" + NumDis + ClienteRec.name.ljust(60)[:60]
                if ClienteRec.vat:
                    Record = Record + ClienteRec.vat[2:] + " " * 4   
                else:
                   Record = Record + ClienteRec.fiscalcode.ljust(16)[:16]  
                Record = Record + " " * 34 + "\r\n" 
                NumeroRecord += 1
                File += Record
                # Inizio Record 40
                #import pdb;pdb.set_trace()
                idsAddress = self.pool.get('res.partner').address_get(cr, uid, [ClienteRec.id], ['default', 'invoice',])
                # self.pool.get('res.partner.address').search(cr,uid,[('partner_id','=',ClienteRec.id),('type','in',['default','invoice'])])
                
                if idsAddress.get('default',False):
                    ClAddress = self.pool.get('res.partner.address').browse(cr,uid,idsAddress['default'])
                #ClAddress = ClienteRec.address[0]
                    clind = ClAddress.street.ljust(30)[:30]
                    cap = ClAddress.zip.rjust(5, "0")[:5]
                    if ClAddress.province.code :
                        loc = ClAddress.city.ljust(21)[:21] + "  " + str(ClAddress.province.code)
                    else:
                            loc = ClAddress.city.ljust(21)[:21]
                else:
                    if idsAddress.get('invoice',False):
                        ClAddress = self.pool.get('res.partner.address').browse(cr,uid,idsAddress['invoice'])
                        clind = ClAddress.street.ljust(30)[:30]
                        cap = ClAddress.zip.rjust(5, "0")[:5]
                        if ClAddress.province.code :
                            loc = ClAddress.city.ljust(21)[:21] + "  " + str(ClAddress.province.code)
                        else:
                            loc = ClAddress.city.ljust(21)[:21]
                    else:  
		                      print "ERRORE NEGLI INDIRIZZI ", ClienteRec.name,ClienteRec.ref
                desban = Effetto.banca_patner.name.ljust(50)[:50]
                Record = " 40" + NumDis + clind + cap + loc + desban + "\r\n" 
                NumeroRecord += 1
                File += Record
                # Inizio Recod 50
                piva = AziendaRec.vat[2:]
                Record = " 50" + NumDis + Effetto.effetto_id.note.ljust(80)[:80] + " " * 10 + piva.ljust(15)[:15] + " " * 4 +  "\r\n" 
                NumeroRecord += 1
                File += Record
                # Inizio Record 51
                Record = " 51" + NumDis + str(Effetto.effetto_id.id).rjust(10, "0")[:10] + DatiAzienda['RagAzi'].ljust(20)[:20] + " " * 80 + "\r\n"
                NumeroRecord += 1
                File += Record
                #Inizio Record 70
                Record = " 70" + NumDis + " " * 110 + "\r\n"
                NumeroRecord += 1
                File += Record
            # Inizio Record EF
            NumeroRecord += 1
            NumRec = str(NumeroRecord).rjust(7, "0")
            diffTot = (TotaleEff - int(TotaleEff))*100
            if diffTot < 10 :
          #import pdb;pdb.set_trace()
                diffTot = '0'+str(diffTot)[0]
            else: 
                diffTot = str(diffTot)[:2]
            ImpTot = str(int(TotaleEff))  + diffTot
            
            Record = " EF" + DatiAzienda['CodiceSia'] + DatiAzienda['Abi'] + DatiAzienda['DataCre'] + DatiAzienda['NomeSupporto'] + " " * 9
            Record = Record + NumDis + ImpTot.rjust(15, "0") + "".rjust(15, '0') + NumRec + " " * 24 + "E" + " " * 6 + "\r\n"
            File += Record
            out = base64.encodestring(File)

        else:
            raise osv.except_osv(_('ERRORE !'), _('Non ci sono Effetti Nella Distinta  '))
      
    
        return self.write(cr, uid, ids, {'state':'get', 'data':out}, context=context)
 

GenFileRiba()

