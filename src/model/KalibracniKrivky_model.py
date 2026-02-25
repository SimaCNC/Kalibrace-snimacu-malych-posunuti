#Trida pro filtraci dat
from typing import TYPE_CHECKING
from tkinter import filedialog
import pandas as pd
from scipy.signal import savgol_filter

if TYPE_CHECKING:
    from controller.main_controller import MainController

class KalibracniKrivkyData():
    def __init__(self, controller : 'MainController'):
        self.controller = controller
        self.data = None
        self.data_vzorky_poradi = []
        self.data_cas = None
        self.data_x = None
        self.data_y = None
        self.data_teplota = None
        self.data_tlak = None
        self.data_vlhkost = None
        self.data_osvetleni = None
        self.typy_dat = ["Frekvence", "Napeti"]
        self.data_typ = None
        self.data_jednotka = None
        self.cesta_soubor = None
        self.pracovni_slozka = None
        self.pocet_vzorku_na_krok = None
        self.pocet_kroku = None
        self.pocet_vzorku = None
        self.blokove_pole = []
        self.metody_filtrace = ["Průměr", "Medián", "MA", "EMA", "S-G","Průměr+EMA"]
        self.data_nahrany = False
        
        self.data_filtrovane = []
        self.osa_filtrovane = []
        
        self.alphaEMA = 1
        self.oknoSG = 11
        self.exponent = 1
                
    def priradit_data(self,typ,jednotka):
        self.data_typ = typ
        self.data_jednotka = jednotka
        self.data_x = self.data.iloc[:,1]
        self.data_y = self.data.iloc[:,2]
        self.data_teplota = self.data.iloc[:,3]
        self.data_tlak = self.data.iloc[:,4]
        self.data_vlhkost = self.data.iloc[:,5]
        self.data_osvetleni = self.data.iloc[:,6]
        cas_series = self.data.iloc[:, 0]
        cas_dt = pd.to_datetime(cas_series, format="%H:%M:%S.%f")
        cas_offset = cas_dt - cas_dt.iloc[0]
        self.data_cas = cas_offset.dt.total_seconds()
        self.data_vzorky_poradi = list(range(1, len(self.data) + 1))
        self.vypocitej_pocet_vzorku_na_krok() #ODPOVIDA POCTU VZORKU NA KROK
        self.vypocitej_pocet_vzorku() #ODPOVIDA POCTU VZORKU V SADE
        self.vypocitej_pocet_kroku() #ODPOVIDA POCTU KROKU V SADE ..... TYTO INFORMACE BY MELY BYT STEJNE JAKO V MD001
        self.vytvor_blokove_pole()
                
        print(f"[{self.__class__.__name__}] DATA PRIRAZENA")

    def nahrat_data(self):
        self.cesta_soubor = filedialog.askopenfilename(title="Data pro filtraci", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not self.cesta_soubor:
            return
        
        try:
            excel_soubor = pd.ExcelFile(self.cesta_soubor)    
            preferovane_listy = ["MD005", "Data"]
            sheet = next((s for s in preferovane_listy if s in excel_soubor.sheet_names), None)

            if sheet is None:
                print(f"[{self.__class__.__name__}] Soubor neobsahuje listy MD005 ani Data!")
                return

            self.data = pd.read_excel(self.cesta_soubor, sheet_name=sheet)
            
            if "Napětí (V)" in self.data.columns:
                print(f"[{self.__class__.__name__}] TYP DAT NAPETI")
                self.priradit_data(typ="napětí", jednotka="(V)")
                   
            elif "Frekvence (Hz)" in self.data.columns:
                print(f"[{self.__class__.__name__}] TYP DAT FREKVENCE")
                self.priradit_data(typ="frekvence", jednotka="(Hz)")
                
            #pokud soubor nesedi - vypnout
            else:
                print(f"[{self.__class__.__name__}] nepodporovany typ dat")
                self.data_nahrany = False
                return
            
            print(f"[{self.__class__.__name__}] USPESNE NAHRANY DATA ZE SOBORU !!!")
            self.data_nahrany = True
            
        except FileNotFoundError:
            print(f"[{self.__class__.__name__}] Soubor neexistuje!")
        except Exception as e:
            print(f"[{self.__class__.__name__}] Chyba pri nacteni souboru: {e}")
            
    def vybrat_pracovni_slozku(self):
        self.pracovni_slozka = filedialog.askdirectory(title="Pracovní složka")
        print(f"[{self.__class__.__name__}] složka {self.pracovni_slozka}")
        
    def vypocitej_pocet_kroku(self):
        if (self.pocet_vzorku or self.pocet_vzorku_na_krok) is None:
            return
        
        self.pocet_kroku = self.pocet_vzorku / self.pocet_vzorku_na_krok # JE O 1 VYSSI NEZ V MD001 PROTOZE SE MERI I POLOHA 0
        print(f"[{self.__class__.__name__}] Pocet kroku = {self.pocet_kroku}")
    
    def vypocitej_pocet_vzorku_na_krok(self):
        if self.data_x is None:
            return
        
        self.pocet_vzorku_na_krok = (self.data_x == self.data_x.iloc[0]).cumprod().sum()
        print(f"[{self.__class__.__name__}] Pocet vzorku na krok = {self.pocet_vzorku_na_krok}")
    
    def vypocitej_pocet_vzorku(self):
        if self.data_vzorky_poradi is None:
            return
        
        self.pocet_vzorku = len(self.data_vzorky_poradi)
        print(f"[{self.__class__.__name__}] Pocet vzorku = {self.pocet_vzorku}")
        
    def vytvor_blokove_pole(self):
        if self.data_x is None:
            return

        self.blokove_hodnoty = self.data_x[self.data_x.ne(self.data_x.shift()).fillna(True)].to_list()
        print(f"[{self.__class__.__name__}] Blokove hodnoty : {self.blokove_hodnoty}")
    
    
    def filtrovani_prumer(self):
        self.data_filtrovane = []
        pocet_kroku = int(self.pocet_kroku)
        pocet_vzorku_na_krok = int(self.pocet_vzorku_na_krok)

        for i in range(pocet_kroku):
            start = i * pocet_vzorku_na_krok
            end = start + pocet_vzorku_na_krok
            blok = self.data_y[start:end]
            prumer = blok.mean()
            self.data_filtrovane.append(round(prumer,6))

        #uprava filtrovane osy
        self.osa_filtrovane = []
        self.osa_filtrovane = self.blokove_hodnoty
        self.zarovnej_osy()
        print(f"[{self.__class__.__name__}] filtrovane (prumer): {self.data_filtrovane}")
        print("LEN X:", len(self.osa_filtrovane), "LEN Y:", len(self.data_filtrovane))
        
    def filtrovani_median(self):
        self.data_filtrovane = []
        pocet_kroku = int(self.pocet_kroku)
        pocet_vzorku_na_krok = int(self.pocet_vzorku_na_krok)

        for i in range(pocet_kroku):
            start = i * pocet_vzorku_na_krok
            end = start + pocet_vzorku_na_krok

            blok = self.data_y[start:end]
            median = blok.median()  
            self.data_filtrovane.append(round(median, 6))

        #uprava filtrovane osy
        self.osa_filtrovane = []
        self.osa_filtrovane = self.blokove_hodnoty
        self.zarovnej_osy()
        print(f"[{self.__class__.__name__}] filtrovane (median): {self.data_filtrovane}")
        print("LEN X:", len(self.osa_filtrovane), "LEN Y:", len(self.data_filtrovane))
        
    def filtrovani_MA(self, okno=20):
        self.data_filtrovane=[]
        self.data_filtrovane = self.data_y.rolling(window=okno, min_periods=1).mean()
        self.data_filtrovane = self.data_filtrovane.round(6).tolist()
        self.osa_filtrovane = []
        self.osa_filtrovane = self.data_x
        self.zarovnej_osy()
        print(f"[{self.__class__.__name__}] filtrovane (MA): {self.data_filtrovane}")
        print("LEN X:", len(self.osa_filtrovane), "LEN Y:", len(self.data_filtrovane))
        
    def filtrovani_EMA(self, okno = 20):
        self.data_filtrovane=[]
        self.data_filtrovane = self.data_y.ewm(span=okno, adjust=False).mean().round(6).tolist()
        self.osa_filtrovane = []
        self.osa_filtrovane = self.data_x
        self.zarovnej_osy()
        print(f"[{self.__class__.__name__}] filtrovane (EMA): {self.data_filtrovane}")
        print("LEN X:", len(self.osa_filtrovane), "LEN Y:", len(self.data_filtrovane))
        
    def filtrovani_SG(self, okno=11, poly=2):
        if self.data_y is None:
            return

        filtrovane = savgol_filter(self.data_y, window_length=okno, polyorder=poly)

        self.data_filtrovane = filtrovane.round(6).tolist()
        self.osa_filtrovane = self.data_x[:len(self.data_filtrovane)]
        self.zarovnej_osy()

        print(f"[{self.__class__.__name__}] filtrovane (S-G): {self.data_filtrovane}")
        print("LEN X:", len(self.osa_filtrovane), "LEN Y:", len(self.data_filtrovane))
        
    def filtrovani_prumer_EMA(self):
        # self.filtrovani_prumer()
        # self.data_filtrovane = pd.Series(self.data_filtrovane).ewm(span=self.alphaEMA, adjust=False).mean().round(6).tolist()
         # 1) EMA na syrová data
        ema = self.data_y.ewm(alpha=self.alphaEMA, adjust=False).mean()

        self.data_filtrovane = []
        pocet_kroku = int(self.pocet_kroku)
        pocet_vzorku_na_krok = int(self.pocet_vzorku_na_krok)

        for i in range(pocet_kroku):
            start = i * pocet_vzorku_na_krok
            end = start + pocet_vzorku_na_krok
            blok = ema[start:end]
            prumer = blok.mean()
            self.data_filtrovane.append(round(prumer, 6))

        self.osa_filtrovane = self.blokove_hodnoty
        self.zarovnej_osy()
        
        print(f"[{self.__class__.__name__}] filtrovane (prumer+EMA): {self.data_filtrovane}")
        print("LEN X:", len(self.osa_filtrovane), "LEN Y:", len(self.data_filtrovane)) 
    
    def filtrovani_prumer_EMA_SG(self):
        self.filtrovani_prumer_EMA()

        self.data_filtrovane = savgol_filter(self.data_filtrovane, window_length=self.oknoSG, polyorder=self.exponent)
        self.zarovnej_osy()
        print("LEN X:", len(self.osa_filtrovane), "LEN Y:", len(self.data_filtrovane))
        print("alphaEMA:", self.alphaEMA, type(self.alphaEMA))
        print("oknoSG:", self.oknoSG, type(self.oknoSG))
        print("exponent:", self.exponent, type(self.exponent))
    
    def zarovnej_osy(self):
        n = min(len(self.data_filtrovane), len(self.osa_filtrovane))
        self.data_filtrovane = list(self.data_filtrovane[:n])
        self.osa_filtrovane = list(self.osa_filtrovane[:n])
