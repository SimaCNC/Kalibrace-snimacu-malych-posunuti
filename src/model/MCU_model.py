from typing import TYPE_CHECKING
import re
import threading
import math

if TYPE_CHECKING:
    from model.Serial_model import SerialCtrl

class MCU_model():
    def __init__(self, mcu_serial : 'SerialCtrl'):
        self.mcu_serial = mcu_serial 
        self.lock_ad = True #odemknuto
        self.lock_frekvence = True #odemknuto
        self.napeti_vzorky = []
        self.frekvence_vzorky = []
        self.teplota_vzorky = []
        self.tlak_vzorky = []
        self.vlhkost_vzorky = []
        self.osvetleni_vzorky = []
        
        self.posledni_odpoved_MCU = None
        self.teplota_okoli = None
        self.typ_mereni = {
            "A/D" : "A/D",
            "OSC" : "OSC"
        }        
        
        self.vzorky = 10
      
    def msg_odpoved(self, callback_fun = None):
        """ odpoved od MCU"""
        
        def msg_odpoved_thread():
            while True:
                try:
                    self.posledni_odpoved_MCU = self.mcu_serial.get_msg_simple()
                    if self.posledni_odpoved_MCU:
                        print(f"[MCU_model]: prichozi zprava {self.posledni_odpoved_MCU}")                      
                    if callback_fun:
                        callback_fun() 
                    break
                except Exception as e:
                    print(f"[MCU_model] chyba pri cteni nebo parsovani dat {e}")  
                    break
        self.t1 = threading.Thread(target=msg_odpoved_thread, daemon=True)
        self.t1.start()
        
        
    def precti_teplotu(self):
        self.mcu_serial.send_msg_simple("#T")
        self.msg_odpoved(self.zapsat_teplotu)
        
    def zapsat_teplotu(self):
        self.teplota_okoli = self.posledni_odpoved_MCU
    
    #cteni frekvence pres UART, n je pocet mereni frekvence (=pocet vzorku)
    def precist_frekvenci(self, pocet_vzorku : int):
        self.n = pocet_vzorku
        self.frekvence_vzorky.clear()
        self.teplota_vzorky.clear()
        self.tlak_vzorky.clear()
        self.vlhkost_vzorky.clear()
        self.osvetleni_vzorky.clear()
        
        #vytvoreni zpravy pro n pocet mereni
        self.lock_frekvence = False
        self.mcu_serial.ser.reset_input_buffer()
        
        def cteni_frekvence():
            
            while len(self.frekvence_vzorky) < self.n:
                try:
                    #jeden prichozi vzorek
                    data_raw = self.mcu_serial.ser.readline().decode().strip()
                    freq = self.dekodovat('f', data_raw)
                    teplota = self.dekodovat('t', data_raw)
                    tlak = self.dekodovat('p', data_raw)
                    vlhkost = self.dekodovat('h', data_raw)
                    osvetleni = self.dekodovat('l', data_raw)
                    if freq is not None:
                        self.frekvence_vzorky.append(freq)
                    else:
                        self.frekvence_vzorky.append(math.nan)
                        print(f"[{self.__class__.__name__} příchozí frekvence: {freq} -- CHYBA!!]")
                        
                    if teplota is not None:
                        self.teplota_vzorky.append(teplota)
                    else:
                        self.teplota_vzorky.append(math.nan)

                    if tlak is not None:
                        self.tlak_vzorky.append(tlak)
                    else:
                        self.tlak_vzorky.append(math.nan)

                    if vlhkost is not None:
                        self.vlhkost_vzorky.append(vlhkost)
                    else:
                        self.vlhkost_vzorky.append(math.nan)
                        
                    if osvetleni is not None:
                        self.osvetleni_vzorky.append(osvetleni)
                    else:
                        self.osvetleni_vzorky.append(math.nan)
                      
                except Exception as e:
                    print(f"[{self.__class__.__name__}] {e} -- CHYBA!!")

            self.lock_frekvence = True
            
            
        self.t1 = threading.Thread(target=cteni_frekvence, daemon=True)
        self.t1.start()
        
        msg = f"#D{self.n}"
        self.mcu_serial.send_msg_simple(msg) 
            
    #cteni napeti na AD pres UART, n je pocet mereni AD,napeti (=pocet vzorku)
    def precist_AD(self, pocet_vzorku : int):
        self.n = pocet_vzorku
        self.napeti_vzorky.clear()
        self.teplota_vzorky.clear()
        self.tlak_vzorky.clear()
        self.vlhkost_vzorky.clear()
        self.osvetleni_vzorky.clear()
        
        #vytvoreni zpravy pro n pocet mereni
        self.lock_ad = False
        self.mcu_serial.ser.reset_input_buffer()
        
        def cteni_napeti():
            
            while len(self.napeti_vzorky) < self.n:
                try:
                    #jeden prichozi vzorek
                    data_raw = self.mcu_serial.ser.readline().decode().strip()
                    napeti = self.dekodovat('v', data_raw)
                    teplota = self.dekodovat('t', data_raw)
                    tlak = self.dekodovat('p', data_raw)
                    vlhkost = self.dekodovat('h', data_raw)
                    osvetleni = self.dekodovat('l', data_raw)
                    if napeti:
                        self.napeti_vzorky.append(napeti)
                    else:
                        self.frekvence_vzorky.append(napeti)
                        print(f"[{self.__class__.__name__} příchozí napeti: {napeti} -- CHYBA!!]")  
                          
                    if teplota is not None:
                        self.teplota_vzorky.append(teplota)
                    else:
                        self.teplota_vzorky.append(math.nan)

                    if tlak is not None:
                        self.tlak_vzorky.append(tlak)
                    else:
                        self.tlak_vzorky.append(math.nan)

                    if vlhkost is not None:
                        self.vlhkost_vzorky.append(vlhkost)
                    else:
                        self.vlhkost_vzorky.append(math.nan)
                        
                    if osvetleni is not None:
                        self.osvetleni_vzorky.append(osvetleni)
                    else:
                        self.osvetleni_vzorky.append(math.nan)
                    
                except Exception as e:
                    print(f"[{self.__class__.__name__}] {e} -- CHYBA!!")
            
            self.lock_ad = True
        
        self.t1 = threading.Thread(target=cteni_napeti, daemon=True)
        self.t1.start()
        
        msg = f"#A{self.n}"
        self.mcu_serial.send_msg_simple(msg)
            
    def dekodovat(self, typ, data):
        self.typ = typ
        self.data = data
        
        #dekodovani frekvence ze stringu:
        if (self.typ == 'f'):
            #priklad prichozi zpravy string data: D=920, F=156521, T=24.6, P=99748.5, H=54.6 <\r><\n> - hterm
            #tvoreny string v C:snprintf(gu8_MSG, sizeof(gu8_MSG), "delta=%d, F=%d Hz\r\n", delta, (uint32_t)freq);
            #chci vytahnout jen to cislo za F= , popripade i staci delta jenom a dopocitat frekvenci v PC
            #hledat F= cislo
            match = re.search(r'F=(\d+)', self.data)
            if match:
                return(int(match.group(1)))
            else:
                print(f"[{self.__class__.__name__}] NEDEKODOVANA FREKVENCE -- CHYBA !!")
                return 0
        
        elif (self.typ == 'v'):
            match = re.search(r'V=(\d+(?:\.\d+)?)', self.data)
            if match:
                return(float(match.group(1)))
            else:
                print(f"[{self.__class__.__name__}] NEDEKODOVANE NAPETI -- CHYBA !!")
                return 0
                
        elif (self.typ == 't'):
            match = re.search(r'T=(\d+(?:\.\d+)?)', self.data)
            if match:
                return(float(match.group(1)))
            else:
                print(f"[{self.__class__.__name__}] NEDEKODOVANA TEPLOTA -- CHYBA !!")
                return 0
        
        elif (self.typ == 'p'):
            match = re.search(r'P=(\d+(?:\.\d+)?)', self.data)
            if match:
                return(float(match.group(1)))
            else:
                print(f"[{self.__class__.__name__}] NEDEKODOVANA TLAK -- CHYBA !!")
                return 0
            
        elif (self.typ == 'h'):
            match = re.search(r'H=(\d+(?:\.\d+)?)', self.data)
            if match:
                return(float(match.group(1)))
            else:
                print(f"[{self.__class__.__name__}] NEDEKODOVANA VLHKOST -- CHYBA !!")
                return 0
            
        elif (self.typ == 'l'):
            match = re.search(r'L=(\d+)', self.data)
            if match:
                return(float(match.group(1)))
            else:
                print(f"[{self.__class__.__name__}] NEDEKODOVANE OSVETLENI -- CHYBA !!")
                return 0
            
        return None