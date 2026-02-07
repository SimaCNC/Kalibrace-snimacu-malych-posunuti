import serial.tools.list_ports
import time
import re

class SerialCtrl():
    
    def __init__(self):
        self.com_list = []
        self.sync_cnt = 200
        self.ser = None
        self.status = False
        self.lock = True
        
    #METODA PRO VYPSANI AKTUALNICH DOSTUPNYCH COM PORTU
    def getCOMlist(self):
        ports = serial.tools.list_ports.comports()
        self.com_list = [com[0] for com in ports]
        self.com_list.insert(0, "-")
        
    #METODA PRO OTEVRENI SERIOVEHO PORTU SE ZVOLENYM BAUDEM A PORTEM
    def SerialOpen(self, port, baud):
        try:
            if self.ser is None or not self.ser.is_open:
                self.ser = serial.Serial(port=port, baudrate=baud, timeout=0.1)
                self.status = True
                print(f"Port {port} byl otevren s baudratem {baud}")
                
            else:
                print(f"Port {port} byl jiz drive otevren")
                self.status = True
                
        except Exception as e:
            print(f"Chyba pri otevirani portu {port}: {e}")
            self.status = False
                   
    
    #METODA PRO ZAVRENI ZVOLENEHO SERIOVEHO PORTU
    def SerialClose(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.status = False
            print(f"Port {self.ser.port} byl uzavren")
        else:
            print(f"Port nebyl otevren, nelze zavrit")
            
    # METODY PRO POSILANI a PRIJEM DAT - PIEZO
    def send_msg_simple(self, msg : str):
        print(f"[SerialCtrl]: odeslana zprava: {msg}")
        self.ser.write(msg.encode())
        
    def get_msg_simple(self, callback = None): #CALLBACK JE FUNKCE, KTERA JE VLOZENA JAKO ARGUMENT - FLEXIBILNI POUZITI FUNKCE get_msg_simple!!
        try:
            data = None
            data = self.ser.readline().decode().strip() 
                
            if data:
                print(f"[SerialCtrl]:přijaté data: {data}")
                if callback:
                    callback(data)
            else:
                print("[SerialCtrl]: nebyla prijata zadne data - timeout")
            return data
        except Exception as e:
            print(f"[SerialCtrl]: chyba pri cteni dat: {e}")
            
    def get_msg_stream(self,send, expect_regex, callback_fun = None):
        try:
            while True:
                self.lock = False
                time.sleep(0.0001)
                self.send_msg_simple(send)
                print(f"odeslane: {send}")
                time.sleep(0.0001)
                msg_received = self.ser.readline().decode().strip()
                print(f"[stream] Prijato: {msg_received}, ocekavane {expect_regex}")
                
                #POKUD PRIJDE HLASKA S CHYBOU err. 9
                if msg_received.startswith("$RS"):
                #cisla po x y z
                    match = re.search(r"x(\d+)\s+y(\d+)\s+z(\d+)", msg_received)
                    if match:
                        x_val, y_val, z_val = match.groups()
                        if "9" in (x_val, y_val, z_val):
                            print(f"{self.__class__.__name__} CHYBA 9 !!! PIEZOPOHONY! NUTNO VYPNOUT A ZAPNOUT PIEZOPOHONY")
                            
                if re.match(expect_regex, msg_received):
                    print(f"[stream] NALEZENO V PRIJATE MSG: {msg_received}, Z OCEKAVANE {expect_regex}")                   
                    if callback_fun:
                        callback_fun(msg_received)
                        time.sleep(0.01)
                    self.lock = True #odemknuto
                    break #konec vlakna
                else:
                    continue
        except Exception as e:
            print(f"chyba: {e}")            