from tkinter import *
from tkinter import ttk
from typing import TYPE_CHECKING
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import matplotlib.pyplot as plt
import webbrowser
from view.kalibrace_view import KalibracniOkno
from model.KalibracniKrivky_model import KalibracniKrivkyData
import sys
import mplcursors
if TYPE_CHECKING:
    from model.Piezo_model import Piezo_model
    from model.MCU_model import MCU_model
    from controller.main_controller import MainController
    
#-----------------------------------------------------     
#KORENOVE OKNO - VYTVORENI INSTANCE TK V ATRIBUTU ROOT    
#----------------------------------------------------- 
class RootGUI():
    def __init__(self):
        self.root : Tk = Tk()
        
        self.root.iconbitmap('template/icon/logo.ico')
        self.root.title("Kalibrace snímačů malých posunutí")
        self.root.geometry("1250x800")
        self.root.config(bg="white")
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.container = Frame(self.root)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {} #ukladani jednotlivych pohledu
        
        #zavreni okna
        self.root.protocol("WM_DELETE_WINDOW", self.window_exit)
        
        #vytvoreni menu
        self.menu = Menu(self.root)
        self.menu.add_command(label="Připojení", command=lambda: self.show_frame("main"))      
        self.menu.add_command(label="Ovládání", command=lambda: self.show_frame("ovladani"))
        self.menu.add_command(label="Kalibrace", command=lambda: self.show_frame("kalibrace"))
        self.menu.add_command(label="Data", command=lambda : self.show_frame("data"))
        self.menu.add_command(label="Kalibrační křivky", command=lambda : self.show_frame("kalibrační křivky"))
        self.menu.add_command(label="Nápověda", command=lambda : webbrowser.open('https://github.com/SimaCNC/Kalibrace-snimacu-malych-posunuti'))
        self.menu.add_command(label="Konec", command=self.window_exit)
        
        self.root.config(menu=self.menu)
        
    def add_frame(self, name, frame_class, *args):
        frame : Frame = frame_class(self.container, *args)
        self.frames[name] = frame 
        frame.grid(row = 0, column = 0, sticky = "nsew")
            
    def show_frame(self, name):
        if name in self.frames:
            self.frames[name].tkraise()
            if name == "filtrace":
                self.root.geometry("1250x1000")
            else:
                self.root.geometry("1250x800")
        else:
            print(f"[frame] Frame '{name}' NEEXISTUJE")
        
    def window_exit(self):
        # zavrit = messagebox.askyesno("Ukončení aplikace", "Přejete si ukončit aplikaci?")
        # if zavrit:
        #     print("Zavirani okna a vypnuti aplikace")
        #     self.root.destroy()
        self.root.destroy()
        sys.exit(0)
        print("Zavirani okna a vypnuti aplikace")

#-----------------------------------------------------     
#TRIDA PRO VYTVORENI SCROLLOVACICH OKEN - FRAME
#----------------------------------------------------- 
class ScrollableFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.canvas = Canvas(self, bg="white")
        self.scrollable_frame = Frame(self.canvas, bg="white")
        
        # Scrollbary
        self.v_scrollbar = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
    
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        # self.canvas.bind("<Configure>", self._on_canvas_configure)  
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))   # Linux 

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            # if self.canvas.winfo_exists():
            #     self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
            if self.canvas.winfo_exists():
                first, last = self.canvas.yview()
                delta = int(-1 * (event.delta / 120))

                if (delta < 0 and first <= 0) or (delta > 0 and last >= 1):
                    return

                self.canvas.yview_scroll(delta, "units")
            
        except TclError:
            pass  

#-------------------------------------------------------------------------        
#PRVNI OKNO APLIKACE (main) - PRIPOJENI A OVLADANI SUBSYSTEMU PIEZA A MCU
#SPRAVOVANI PRIPOJENI K SERIOVYM KOMUNIKACIM PRO MCU A PIEZOPOHONY 
#OVLADANI PRO UMISTENI SENZORU   
#------------------------------------------------------------------------- 
class MainPage(ScrollableFrame):
    def __init__(self, parent, controller : 'MainController', piezo_model, mcu_model):
        super().__init__(parent)
        self.config(bg="white")

        self.com_gui : LabelFrame = ComGUI(self.scrollable_frame, controller, piezo_model, mcu_model)
        self.com_gui.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        
        self.controler = controller
        self.controler.set_main_page(self)
        
class ComGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController', piezo_model : 'Piezo_model', mcu_model : 'MCU_model'):
        super().__init__(parent, text="COM manažer připojení", padx=5, pady=5, bg="white",fg="black",bd=5, relief="groove")
        self.controller = controller
        self.piezo_model = piezo_model
        self.mcu_model = mcu_model
        
        #LEVE OKNA - COM PRIPOJENI 
        self.frame_piezo = LabelFrame(self, text="Piezopohony", padx=5, pady=5, bg="white")
        self.frame_MCU = LabelFrame(self, text="MCU", padx=5, pady=5, bg="white")
        
        #LEVE OKNA - PRVKY
        self.label_com_piezo = Label(self.frame_piezo, text="Dostupné porty:", bg="white", width=15, anchor="w")
        self.label_bd_piezo = Label(self.frame_piezo, text="Baud rate:", bg="white", width=15, anchor="w")
        self.btn_refresh_piezo = Button(self.frame_piezo, text="Obnovit", width=10, command=self.com_refresh_piezo)
        self.btn_connect_piezo = Button(self.frame_piezo, text="Připojit", width=10, state="disabled", command=self.controller.M_serial_connect_piezo)
        self.Com_option_piezo()
        self.Baud_option_piezo()
        
        self.label_com_MCU = Label(self.frame_MCU, text="Dostupné porty: ", bg="white", width=15, anchor="w")
        self.label_bd_MCU = Label(self.frame_MCU, text="Baud rate:", bg="white", width=15, anchor="w")
        self.btn_refresh_MCU = Button(self.frame_MCU, text="Obnovit", width=10, command=self.com_refresh_MCU)
        self.btn_connect_MCU = Button(self.frame_MCU, text="Připojit", width=10, state="disabled", command=self.controller.M_serial_connect_MCU)
        self.Com_option_MCU()
        self.Baud_option_MCU()
        
        self.publish()
        #LEVE OKNA - COM PRIPOJENI
        
    def publish(self):
        #LEVE OKNA - COM PRIPOJENI
        # self.grid(row=0, column=0, padx=5, pady=5, sticky="NW")
        self.frame_piezo.grid(row=0, column=0, padx=5, pady=5)
        self.frame_MCU.grid(row=1, column=0, padx=5, pady=5)
        
        #LEVE OKNA PRVKY
        self.label_com_piezo.grid(row=0, column=0, padx=5, pady=5)
        self.label_bd_piezo.grid(row=1, column=0, padx=5, pady=5)
        self.btn_refresh_piezo.grid(row=0, column=2, padx=5, pady=5)
        self.btn_connect_piezo.grid(row=1, column=2, padx=5, pady=5)
        self.drop_com_piezo.grid(row=0, column=1, padx=5, pady=5)
        self.drop_bd_piezo.grid(row=1, column=1, padx=5, pady=5)
        
        self.label_com_MCU.grid(row=0, column=0, padx=5, pady=5)
        self.label_bd_MCU.grid(row=1, column=0, padx=5, pady=5)
        self.btn_refresh_MCU.grid(row=0, column=2, padx=5, pady=5)
        self.btn_connect_MCU.grid(row=1, column=2, padx=5, pady=5)
        self.drop_com_MCU.grid(row=0, column=1, padx=5, pady=5)
        self.drop_bd_MCU.grid(row=1, column=1, padx=5, pady=5)
    
    #LEVE OKNA LOGIKA - COM PRIPOJENI  
    def com_refresh_piezo(self):
        self.drop_com_piezo.destroy()
        self.Com_option_piezo()
        self.drop_com_piezo.grid(row=0, column=1, padx=5, pady=5)
        self.connect_ctrl_piezo("reset")
    
    def com_refresh_MCU(self):
        self.drop_com_MCU.destroy()
        self.Com_option_MCU()
        self.drop_com_MCU.grid(row=0, column=1, padx=5, pady=5)
        self.connect_ctrl_MCU("reset")
        
    def Com_option_piezo(self):
        self.piezo_model.piezo_serial.getCOMlist()
        self.vybrany_com_piezo = StringVar()
        if self.piezo_model.piezo_serial.com_list:
            self.vybrany_com_piezo.set(self.piezo_model.piezo_serial.com_list[0])
        else:
            self.vybrany_com_piezo.set("-")
        self.drop_com_piezo = OptionMenu(self.frame_piezo, self.vybrany_com_piezo, *self.piezo_model.piezo_serial.com_list, command=self.connect_ctrl_piezo)
        self.drop_com_piezo.config(width=10)
        
    def Baud_option_piezo(self):
        self.vybrany_bd_piezo = StringVar()
        bds = ["-", "115200"]
        self.vybrany_bd_piezo.set(bds[0])
        self.drop_bd_piezo = OptionMenu(self.frame_piezo, self.vybrany_bd_piezo, *bds, command=self.connect_ctrl_piezo)
        self.drop_bd_piezo.config(width=10)

    def Com_option_MCU(self):
        self.mcu_model.mcu_serial.getCOMlist()
        self.vybrany_com_MCU = StringVar()
        self.vybrany_com_MCU.set(self.mcu_model.mcu_serial.com_list[0])
        self.drop_com_MCU = OptionMenu(self.frame_MCU, self.vybrany_com_MCU, *self.mcu_model.mcu_serial.com_list, command=self.connect_ctrl_MCU)
        self.drop_com_MCU.config(width=10)
        
    def Baud_option_MCU(self):
        self.vybrany_bd_MCU = StringVar()
        bds = ["-", "9600", "115200"]
        self.vybrany_bd_MCU.set(bds[0])
        self.drop_bd_MCU = OptionMenu(self.frame_MCU, self.vybrany_bd_MCU, *bds, command=self.connect_ctrl_MCU)
        self.drop_bd_MCU.config(width=10)
         
    def connect_ctrl_piezo(self, other):
        if "-" in self.vybrany_com_piezo.get() or "-" in self.vybrany_bd_piezo.get():
            self.btn_connect_piezo["state"] = "disable"
            print("Piezopohony: nutno dovytvorit konfiguraci pripojeni")
        else:
            self.btn_connect_piezo["state"] = "active"
            print("Pripojeni k piezopohonum aktivni")
            
    def connect_ctrl_MCU(self, other):
        if "-" in self.vybrany_com_MCU.get() or "-" in self.vybrany_bd_MCU.get():
            self.btn_connect_MCU["state"] = "disable"
            print("MCU: nutno dovytvorit konfiguraci pripojeni")
        else:
            self.btn_connect_MCU["state"] = "active"
            print("Pripojeni k MCU aktivni")    
 
class OvladaniPage(ScrollableFrame):
    def __init__(self, parent, controller : 'MainController', piezo_model, mcu_model):
        super().__init__(parent)
        self.config(bg="white")    

        self.piezo_gui : LabelFrame = PiezoGUI(self.scrollable_frame, controller, piezo_model)
        self.piezo_gui.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        
        self.mcu_gui : LabelFrame = McuGUI(self.scrollable_frame, controller, mcu_model)
        self.mcu_gui.grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        
        self.controler = controller
        self.controler.set_ovladani_page(self)
    
#SPRAVOVANI PRIPOJENI K SERIOVYM KOMUNIKACIM PRO MCU A PIEZOPOHONY - LEVE HORNI OKNO APLIKACE, trida ComGui()         
class PiezoGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController' ,piezo_model : 'Piezo_model'):
        super().__init__(parent, text="Piezopohony", padx=5, pady=5, bg="white", relief="groove",bd=5)
        self.controller = controller
        self.piezo_model = piezo_model
        
        
        #ovladani
        self.frame_piezo_ovladani = LabelFrame(self,text="Ovládání" ,padx=5, pady=5, bg="white")
        self.frame_piezo_ovladani.grid(row=0, column=0, padx=5, pady=5, sticky="NW") 
        self.frame_piezo_ovladani_leve = Frame(self.frame_piezo_ovladani,padx=5, pady=5, bg="white")
        self.frame_piezo_ovladani_leve.grid(row=0, column=0, padx=5, pady=5, sticky="NW") 
        self.frame_piezo_ovladani_prave = Frame(self.frame_piezo_ovladani,padx=5, pady=5, bg="white")
        self.frame_piezo_ovladani_prave.grid(row=0, column=1, padx=5, pady=5, sticky="NW") 
        
        self.label_index_piezo = Label(self.frame_piezo_ovladani_leve, text="Home pozice:", bg="white", width=20, anchor="w")
        self.label_index_piezo.grid(row=0, column=0, padx=5, pady=5, sticky="NW")
        self.BTN_index_piezo = Button(self.frame_piezo_ovladani_leve, text="HOME", width=10,state="disabled" ,command= self.controller.M_C_Index)#SERIAL - POSLAT INDEX - PRIJEM
        self.BTN_index_piezo.grid(row=0, column=1, padx=5, pady=5, sticky="NW")
        
        
    def publish_PiezoGUI_home_done(self):
        #ovladani
        self.label_piezo_precist_polohu = Label(self.frame_piezo_ovladani_leve, text="Přečíst aktuální polohu:", bg= "white", width=20, anchor="w")
        self.BTN_piezo_precist_polohu = Button(self.frame_piezo_ovladani_leve, text="POLOHA", width=10, command=self.controller.M_C_precti_polohu)
        self.label_reference_piezo = Label(self.frame_piezo_ovladani_leve, text="Nastavit referenční pozici:", bg="white", width=20, anchor="w")
        self.BTN_reference_piezo = Button(self.frame_piezo_ovladani_leve, text="REFERENCE", width=10, command= self.controller.M_C_nastav_referenci)#SERIAL - POSLAT INDEX - PRIJEM
        self.label_rychlost_piezo = Label(self.frame_piezo_ovladani_leve, text="Nastavit rychlost posunu:", bg="white", width=20, anchor="w")
        self.vybrana_rychlost_piezo = StringVar()
        rychlosti = ["10", "100", "500", "1000", "2000", "3000", "4000", "5000", "6000", "8000"]
        self.vybrana_rychlost_piezo.set(rychlosti[6])
        self.drop_rychlost_piezo = OptionMenu(self.frame_piezo_ovladani_leve, self.vybrana_rychlost_piezo, *rychlosti, command=self.piezo_model.nastav_rychlost)
        self.label_kalibracni_poloha_piezo = Label(self.frame_piezo_ovladani_leve, text="Poloha MAX Y", width=25, bg="white", anchor="w")
        self.BTN_kalibracni_poloha_piezo = Button(self.frame_piezo_ovladani_leve, text="MAX Y+", width=10, command=self.controller.M_C_kalibracni_poloha_piezo)
        self.piezo_model.nastav_rychlost(4000)
        
        #ovladani - pohyb
        validace_float = (self.controller.root.register(self.je_float), "%P") #validace dat na float
        self.label_piezo_pohyb = Label(self.frame_piezo_ovladani_prave, text="Nastavit velikost pohybu v μm:", bg="white", width=25, anchor="w")
        self.entry_piezo_pohyb = Entry(self.frame_piezo_ovladani_prave, width=10,validate="key" ,validatecommand=validace_float)
        self.entry_piezo_pohyb.bind("<Return>", lambda _ : self.controller.M_C_nastav_pohyb_piezo(self.entry_piezo_pohyb.get()))
        self.label_piezo_pohyb_nastavene = Label(self.frame_piezo_ovladani_prave, text="Nastavená velikost pohybu v μm:", bg="white", width=25, anchor="w")
        self.label_piezo_pohyb_nastavene_text = Label(self.frame_piezo_ovladani_prave, text=self.piezo_model.velikost_pohybu, bg="white", width=5, anchor="w")
        
        self.frame_piezo_pohyb = Frame(self.frame_piezo_ovladani_prave, padx=5, pady=5, bg="white")
        self.BTN_piezo_pohyb_xP = Button(self.frame_piezo_pohyb, text="X+", width=5, command=lambda: self.controller.M_C_pohyb_piezo("x"))
        self.BTN_piezo_pohyb_xM = Button(self.frame_piezo_pohyb, text="X-", width=5, command=lambda: self.controller.M_C_pohyb_piezo("x-"))
        self.BTN_piezo_pohyb_yP = Button(self.frame_piezo_pohyb, text="Y+", width=5, command=lambda: self.controller.M_C_pohyb_piezo("y"))
        self.BTN_piezo_pohyb_yM = Button(self.frame_piezo_pohyb, text="Y-", width=5, command=lambda: self.controller.M_C_pohyb_piezo("y-"))
        self.BTN_piezo_pohyb_zP = Button(self.frame_piezo_pohyb, text="Z+", width=5, command=lambda: self.controller.M_C_pohyb_piezo("z"))
        self.BTN_piezo_pohyb_zM = Button(self.frame_piezo_pohyb, text="Z-", width=5, command=lambda: self.controller.M_C_pohyb_piezo("z-"))
        
        
        #pozice
        self.frame_piezo_pozice = LabelFrame(self,text="Pozice (μm)", padx=5, pady=5, bg="white")
        self.label_pozice_home_piezo = Label(self.frame_piezo_pozice, text="Pozice od home:", padx=5, pady=5, bg="white", width=15,)
        self.label_pozice_homeX_piezo = Label(self.frame_piezo_pozice, text="Xh:", padx=5, pady=5, bg="white", width=10)
        self.label_pozice_homeY_piezo = Label(self.frame_piezo_pozice, text="Yh:", padx=5, pady=5, bg="white", width=10)
        self.label_pozice_homeZ_piezo = Label(self.frame_piezo_pozice, text="Zh:", padx=5, pady=5, bg="white", width=10)
        self.label_pozice_reference_piezo = Label(self.frame_piezo_pozice, text="Pozice od reference:", padx=5, pady=5, bg="white", width=15,)
        self.label_pozice_referenceX_piezo = Label(self.frame_piezo_pozice, text="Xr:", padx=5, pady=5, bg="white", width=10,)
        self.label_pozice_referenceY_piezo = Label(self.frame_piezo_pozice, text="Yr:", padx=5, pady=5, bg="white", width=10,)
        self.label_pozice_referenceZ_piezo = Label(self.frame_piezo_pozice, text="Zr:", padx=5, pady=5, bg="white", width=10,)
        
        #prikaz
        self.frame_piezo_prikaz = LabelFrame(self,text="Příkaz", padx=5, pady=5, bg="white")
        self.label_piezo_prikaz = Label(self.frame_piezo_prikaz, text="Příkaz k odeslání:", bg="white", width=20, anchor="w")
        self.entry_piezo_prikaz = Entry(self.frame_piezo_prikaz, width=33,)
        self.entry_piezo_prikaz.bind("<Return>", lambda _ : self.controller.M_C_send_msg_piezo(self.entry_piezo_prikaz.get()))
        self.BTN_piezo_prikaz = Button(self.frame_piezo_prikaz, text="POSLAT", width=10, command= lambda: self.controller.M_C_send_msg_piezo(self.entry_piezo_prikaz.get()))
        self.label_piezo_odpoved = Label(self.frame_piezo_prikaz, text="Odpověď piezopohony:", bg="white", width=20, anchor="w")
        self.text_piezo_odpoved = Text(self.frame_piezo_prikaz, width=25, height=1)
        self.BTN_piezo_odpoved = Button(self.frame_piezo_prikaz, text="REFRESH", width=10, command=self.controller.M_C_odpoved_piezo_refresh)
        
        #zavolani
        self.publish()
        
    def publish(self):
        #ovladani
        self.label_reference_piezo.grid(row=1, column=0, padx=5, pady=5, sticky="NW")
        self.BTN_reference_piezo.grid(row=1, column=1, padx=5, pady=5, sticky="NW")
        self.label_piezo_precist_polohu.grid(row=2, column=0, padx=5, pady=5, sticky="NW")
        self.BTN_piezo_precist_polohu.grid(row=2, column=1, padx=5, pady=5, sticky="NW")
        self.label_rychlost_piezo.grid(row=3, column=0, padx=5, pady=5, sticky="NW")
        self.drop_rychlost_piezo.grid(row=3, column=1, padx=5, pady=5, sticky="NW")
        self.drop_rychlost_piezo.config(width=6, padx=5, pady=5)
        self.label_kalibracni_poloha_piezo.grid(row=4, column=0, padx=5, pady=5, sticky="NW")
        self.BTN_kalibracni_poloha_piezo.grid(row=4, column=1, padx=5, pady=5, sticky="NW")
        
        #ovladani - pohyb
        self.label_piezo_pohyb.grid(row=0, column=0, padx=5, pady=5, sticky="NW")
        self.entry_piezo_pohyb.grid(row=0, column=1, padx=5, pady=5, sticky="NW")
        self.label_piezo_pohyb_nastavene.grid(row=1, column=0, padx=5, pady=5, sticky="NW")
        self.label_piezo_pohyb_nastavene_text.grid(row=1, column=1, padx=5, pady=5, sticky="NW")
        
        
        self.frame_piezo_pohyb.grid(row=2, column=0, sticky="NW")
        self.BTN_piezo_pohyb_xP.grid(row=0, column=0, padx=5, pady=5, sticky="NW")
        self.BTN_piezo_pohyb_xM.grid(row=1, column=0, padx=5, pady=5, sticky="NW")
        self.BTN_piezo_pohyb_yP.grid(row=0, column=1, padx=5, pady=5, sticky="NW")
        self.BTN_piezo_pohyb_yM.grid(row=1, column=1, padx=5, pady=5, sticky="NW")
        self.BTN_piezo_pohyb_zP.grid(row=0, column=2, padx=5, pady=5, sticky="NW")
        self.BTN_piezo_pohyb_zM.grid(row=1, column=2, padx=5, pady=5, sticky="NW")
       
        
        #pozice
        self.frame_piezo_pozice.grid(row=1, column=0, padx=5, pady=10, sticky="NW")
        self.label_pozice_home_piezo.grid(row=0, column=0)
        self.label_pozice_homeX_piezo.grid(row=0, column=1, padx=5, pady=5, sticky="NW")
        self.label_pozice_homeY_piezo.grid(row=1, column=1, padx=5, pady=5, sticky="NW")
        self.label_pozice_homeZ_piezo.grid(row=2, column=1, padx=5, pady=5, sticky="NW")
        self.label_pozice_reference_piezo.grid(row=0, column=2)
        self.label_pozice_referenceX_piezo.grid(row=0, column=3, padx=5, pady=5, sticky="NW")
        self.label_pozice_referenceY_piezo.grid(row=1, column=3, padx=5, pady=5, sticky="NW")
        self.label_pozice_referenceZ_piezo.grid(row=2, column=3, padx=5, pady=5, sticky="NW")
        
        #prikaz
        self.frame_piezo_prikaz.grid(row=2, column=0, padx=5, pady=10, sticky="NW")
        self.label_piezo_prikaz.grid(row=0, column=0, padx=5, pady=5, sticky="NW")
        self.entry_piezo_prikaz.grid(row=0, column=1, padx=5, pady=5, sticky="NW")
        self.BTN_piezo_prikaz.grid(row=0, column=2, padx=5, pady=5, sticky="NW")
        self.label_piezo_odpoved.grid(row=1, column=0, padx=5, pady=5, sticky="NW")
        self.text_piezo_odpoved.grid(row=1, column=1, padx=5, pady=5, sticky="NW")
        self.text_piezo_odpoved.config(state="disabled")
        self.BTN_piezo_odpoved.grid(row=1, column=2, padx=5, pady=5, sticky="NW")
        
    def PiezoGUIClose(self):
        self.controller.piezo = False
        self.disable_children(self)
    
    def disable_children(self, widget):
        if isinstance(widget, (Button, Entry)):
            widget.config(state="disabled")   
        elif isinstance(widget, OptionMenu):
            widget.config(state="disabled")
        for child in widget.winfo_children():
                self.disable_children(child)
        
    def PiezoGUIOpen(self):
        self.controller.piezo = True
        self.enable_children(self)
        
    def enable_children(self, widget):     
        if isinstance(widget, (Button, Entry)):
            widget.config(state="normal")     
        elif isinstance(widget, OptionMenu):
            widget.config(state="normal")       
        for child in widget.winfo_children():
            self.enable_children(child)     
        
    def disable_piezo_buttons(self):
        self.BTN_piezo_pohyb_xP.config(state="disabled")
        self.BTN_piezo_pohyb_xM.config(state="disabled")
        self.BTN_piezo_pohyb_yP.config(state="disabled")
        self.BTN_piezo_pohyb_yM.config(state="disabled")
        self.BTN_piezo_pohyb_zP.config(state="disabled")
        self.BTN_piezo_pohyb_zM.config(state="disabled")
        self.BTN_piezo_prikaz.config(state="disabled")
        self.BTN_reference_piezo.config(state="disabled")
        self.BTN_piezo_precist_polohu.config(state="disabled")
        self.BTN_kalibracni_poloha_piezo.config(state="disabled")
        
    def enable_piezo_buttons(self):
        self.BTN_piezo_pohyb_xP.config(state="normal")
        self.BTN_piezo_pohyb_xM.config(state="normal")
        self.BTN_piezo_pohyb_yP.config(state="normal")
        self.BTN_piezo_pohyb_yM.config(state="normal")
        self.BTN_piezo_pohyb_zP.config(state="normal")
        self.BTN_piezo_pohyb_zM.config(state="normal")
        self.BTN_piezo_prikaz.config(state="normal")
        self.BTN_reference_piezo.config(state="normal")
        self.BTN_piezo_precist_polohu.config(state="normal")
        self.BTN_kalibracni_poloha_piezo.config(state="normal")
        
    def je_float(self, vstup):
        if vstup in (""):
            return True
        try:
            float(vstup)
            return True
        except ValueError:
            return False
        
class McuGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController' ,mcu_model : 'MCU_model'):
        super().__init__(parent, text="MCU", padx=5, pady=5, bg="white", relief="groove",bd=5)
        self.controller = controller
        self.mcu_model = mcu_model

        #Ovladani
        self.frame_mcu_prikaz = LabelFrame(self,text="Příkaz" ,padx=5, pady=5, bg="white")
        self.frame_mcu_prikaz.grid(row=0, column=0, padx=5, pady=5, sticky="NW") 
        
        self.label_mcu_odeslat = Label(self.frame_mcu_prikaz, text="Zpráva k odeslání: ", bg="white", width=15, anchor="w")
        self.entry_mcu_prikaz = Entry(self.frame_mcu_prikaz, width=40)
        self.entry_mcu_prikaz.bind("<Return>", lambda _ : self.controller.M_C_send_msg_MCU(self.entry_mcu_prikaz.get()))
        self.BTN_mcu_prikaz = Button(self.frame_mcu_prikaz, text="POSLAT", width=10, command= lambda: self.controller.M_C_send_msg_MCU(self.entry_mcu_prikaz.get()))
        
        self.label_mcu_odpoved = Label(self.frame_mcu_prikaz, text="Odpověď MCU:", bg="white", width=20, anchor="w")
        self.text_MCU_odpoved = Text(self.frame_mcu_prikaz, width=30, height=1)
        self.BTN_mcu_odpoved = Button(self.frame_mcu_prikaz, text="REFRESH", width=10, command= self.controller.M_C_odpoved_MCU_refresh)
        
        self.publish_gui_MCU()
        self.McuGUIClose()
        
    def publish_gui_MCU(self):
        self.label_mcu_odeslat.grid(row=0, column=0, padx=5, pady=5, sticky="NW")
        self.entry_mcu_prikaz.grid(row=0, column=1, padx=5, pady=5, sticky="NW")
        self.BTN_mcu_prikaz.grid(row=0, column=2, padx=5, pady=5, sticky="NW")   
        self.label_mcu_odpoved.grid(row=1, column=0, padx=5, pady=5, sticky="NW") 
        self.text_MCU_odpoved.grid(row=1, column=1, padx=5, pady=5, sticky="NW")
        self.text_MCU_odpoved.config(state="disabled")
        self.BTN_mcu_odpoved.grid(row=1, column=2, padx=5, pady=5, sticky="NW")    
            
    def McuGUIClose(self):
        self.controller.mcu = False
        self.disable_children(self)
    
    def disable_children(self, widget):
        if isinstance(widget, (Button, Entry)):
            widget.config(state="disabled")   
        elif isinstance(widget, OptionMenu):
            widget.config(state="disabled")
        for child in widget.winfo_children():
                self.disable_children(child)
        
    def McuGUIOpen(self):
        self.controller.mcu = True
        self.enable_children(self)
        
    def enable_children(self, widget):     
        if isinstance(widget, (Button, Entry)):
            widget.config(state="normal")     
        elif isinstance(widget, OptionMenu):
            widget.config(state="normal")       
        for child in widget.winfo_children():
            self.enable_children(child)
          
#------------------------------        
#KALIBRACE PAGE    
#------------------------------           
class KalibracePage(ScrollableFrame):
    def __init__(self, parent, controller : 'MainController', piezo_model, mcu_model):
        super().__init__(parent)
        self.config(bg="white")
        
        self.stav_gui : LabelFrame = StavGUI(self.scrollable_frame, controller, piezo_model, mcu_model)
        self.stav_gui.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
                
        self.protokol_gui : LabelFrame = Typ_protokolGUI(self.scrollable_frame, controller, piezo_model, mcu_model)
        self.protokol_gui.grid(row=0, column=1, padx=5, pady=5, sticky="nw")
        
        self.kalibrace_gui : LabelFrame = KalibraceGUI(self.scrollable_frame, controller, piezo_model, mcu_model, )
        self.kalibrace_gui.grid(row=0, column=2, padx=5, pady=5, sticky="nw")
        
        self.controler = controller
        self.controler.set_kalibrace_page(self)

#Frame STAV
class StavGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController', piezo_model : 'Piezo_model', mcu_model : 'MCU_model'):
        super().__init__(parent, text="Stav", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        self.piezo_model = piezo_model
        self.mcu_model = mcu_model
        
        self.label_stav_piezo = Label(self, text="Připojení piezo :", bg="white", width=20, anchor="w")
        self.label_stav_piezo_show = Label(self, text="NEAKTIVNÍ", fg="red", bg="white", width=20, anchor="w")
        self.label_stav_MCU = Label(self, text="Připojení MCU :", bg="white", width=20, anchor="w")
        self.label_stav_MCU_show = Label(self, text="NEAKTIVNÍ", fg="red", bg="white", width=20, anchor="w")
        self.label_teplota = Label(self, text="Teplota okolí senzoru :", bg="white", width=20, anchor="w")
        self.label_teplota_show = Label(self, text="N/A", fg="red", bg="white", width=20, anchor="w")
        
        
        self.label_aktualizace = Label(self, text="Aktualizace :", bg="white", width=20, anchor="w")
        self.BTN_aktualizace = Button(self, text="Aktualizace", width=20, state="active", command=controller.M_C_aktualizace_stav)
        self.publish()
        
    def publish(self):
        self.label_stav_piezo.grid(row=0, column=0, padx=5, pady=5)
        self.label_stav_piezo_show.grid(row=0, column=1, padx=5, pady=5)
        self.label_stav_MCU.grid(row=1, column=0, padx=5, pady=5)
        self.label_stav_MCU_show.grid(row=1, column=1, padx=5, pady=5)
        self.label_teplota.grid(row=2, column=0, padx=5, pady=5)
        self.label_teplota_show.grid(row=2, column=1, padx=5, pady=5)
        
        self.label_aktualizace.grid(row=3, column=0, padx=5, pady=5)
        self.BTN_aktualizace.grid(row=3, column=1, padx=5, pady=5)

#Frame ZPRACOVANI DAT
class Typ_protokolGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController', piezo_model : 'Piezo_model', mcu_model : 'MCU_model'):
        super().__init__(parent, text="Zpracování dat", padx=5, pady=5, bg="white", bd=5, relief="groove")
        self.controller = controller
        self.piezo_model = piezo_model
        self.mcu_model = mcu_model
        
        self.vybrane_var = StringVar(self, value="1")
        #   volby = {"1" : "A/D převodník",
                    #"2" : "Pulzy",
                    #"3" : "Protokol"}
        self.RB_AD = Radiobutton(self, text="A/D převodník: 0...3,3V", variable=self.vybrane_var, value="1",bg="white" ,command=lambda : self.controller.kalibrace.protokol_kalibrace(self.vybrane_var.get()), width=20, anchor="w")
        self.RB_pulzy = Radiobutton(self, text="Pulzy: 0...1MHz", variable=self.vybrane_var, value="2",bg="white" ,command=lambda : self.controller.kalibrace.protokol_kalibrace(self.vybrane_var.get()), width=20, anchor="w")
        self.RB_protokol = Radiobutton(self, text="Protokol", variable=self.vybrane_var, value="3",bg="white" ,command=lambda : self.controller.kalibrace.protokol_kalibrace(self.vybrane_var.get()), width=20, anchor="w")   
            
        self.publish()
        
    def publish(self):
        self.RB_AD.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        self.RB_pulzy.grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.RB_protokol.grid(row=2, column=0, padx=5, pady=5, sticky="nw")

#Frame KALIBRACE
class KalibraceGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController', piezo_model : 'Piezo_model', mcu_model : 'MCU_model'):
        super().__init__(parent, text="Kalibrace", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        self.piezo_model = piezo_model
        self.mcu_model = mcu_model
        
        #pridat pocet vzorku na pozici
        
        self.label_slozka = Label(self, text="Pracovní složka :", bg="white", width=20, anchor="w")
        self.Entry_slozka_pracovni = Entry(self, width=30, state="normal")
        self.Entry_slozka_pracovni.insert(0, "N/A")
        self.Entry_slozka_pracovni.config(state="readonly")
        self.BTN_slozka_pracovni = Button(self, text="SLOŽKA", width=18, state="active", command=self.controller.kalibrace.vybrat_pracovni_slozku)
        
        self.label_strategie = Label(self, text="Strategie kalibrace :", bg="white", width=20, anchor="w")
        self.label_strategie_vybrana = Label(self, text="N/A", bg ="white", width=30, anchor="w")
        self.strategie = ["-", "Dopředná", "Zpětná","Opakovatelnost", "Hystereze", "Hystereze_2" ]
        self.vybrany_drop_strategie = StringVar()
        self.vybrany_drop_strategie.set("-")
        self.drop_strategie = OptionMenu(self, self.vybrany_drop_strategie, *self.strategie,command=lambda value: self.label_strategie_vybrana.config(text=value))
        self.drop_strategie.config(width=15)
        
        #validace- omezeni na cislo float a int
        validace_float = (self.controller.root.register(self.je_float), "%P")
        validace_int = (self.controller.root.register(self.je_int), "%P")
        
        self.label_krok = Label(self, text="Délka kroku (μm) :", bg="white", width=20, anchor="w")
        self.entry_krok = Entry(self, width=30, validate="key", validatecommand=validace_float)
        self.entry_krok.insert(0, "100")
        self.entry_krok.bind("<Return>", lambda _ : self.controller.kalibrace.nastavit_delku_kroku(self.entry_krok.get()))
        self.BTN_krok = Button(self, text="Potvrdit", width=18, command= lambda: self.controller.kalibrace.nastavit_delku_kroku(self.entry_krok.get()))
        self.controller.kalibrace.nastavit_delku_kroku(self.entry_krok.get())
        
        self.label_vzdalenost = Label(self, text="Měřená vzdálenost (μm) :", bg="white", width=20, anchor="w")
        self.entry_vzdalenost = Entry(self, width=30, validate="key", validatecommand=validace_float)
        self.entry_vzdalenost.insert(0, "1000")
        self.entry_vzdalenost.bind("<Return>", lambda _ : self.controller.kalibrace.nastavit_delku_vzdalenost(self.entry_vzdalenost.get()))
        self.BTN_vzdalenost = Button(self, text="Potvrdit", width=18, command=lambda: self.controller.kalibrace.nastavit_delku_vzdalenost(self.entry_vzdalenost.get()))
        self.controller.kalibrace.nastavit_delku_vzdalenost(self.entry_vzdalenost.get())
        
        self.label_pocet_vzorku = Label(self, text="Počet vzorků :", bg="white", width=20, anchor="w")
        self.entry_pocet_vzorku = Entry(self, width=30, validate="key", validatecommand=validace_int)
        self.entry_pocet_vzorku.insert(0, "10")
        self.entry_pocet_vzorku.bind("<Return>", lambda _ : self.controller.kalibrace.nastavit_vzorky(self.entry_pocet_vzorku.get()))
        self.BTN_pocet_vzorku = Button(self, text="Potvrdit", width=18, command= lambda: self.controller.kalibrace.nastavit_vzorky(self.entry_pocet_vzorku.get()))
        self.controller.kalibrace.nastavit_vzorky(self.entry_pocet_vzorku.get())
        
        self.label_kalibraceStart = Label(self, text="Start kalibrace :", bg="white", width=20, anchor="e")
        self.BTN_kalibraceStart = Button(self, text="START", width=18, state="active", command= self.BTN_kalibraceStart_nastavit)
         
        self.publish()
        
    def BTN_kalibraceStart_nastavit(self):
            self.controller.kalibrace.nastavit_delku_kroku(self.entry_krok.get())
            self.controller.kalibrace.nastavit_delku_vzdalenost(self.entry_vzdalenost.get())
            self.controller.kalibrace.nastavit_vzorky(self.entry_pocet_vzorku.get())
            self.okno_kalibrace()
        
    def publish(self):
        self.label_slozka.grid(row=0, column=0, padx=5, pady=5)
        self.Entry_slozka_pracovni.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.BTN_slozka_pracovni.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        self.label_strategie.grid(row=1, column=0, padx=5, pady=5)
        self.label_strategie_vybrana.grid(row=1, column=1, padx=5, pady=5)
        self.drop_strategie.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        self.label_krok.grid(row=2, column=0, padx=5, pady=5)
        self.entry_krok.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.BTN_krok.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        self.label_vzdalenost.grid(row=3, column=0, padx=5, pady=5)
        self.entry_vzdalenost.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.BTN_vzdalenost.grid(row=3, column=2, padx=5, pady=5, sticky="w")
        
        self.label_pocet_vzorku.grid(row=4, column=0, padx=5, pady=5)
        self.entry_pocet_vzorku.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.BTN_pocet_vzorku.grid(row=4, column=2, padx=5, pady=5, sticky="w")  

        self.label_kalibraceStart.grid(row=6, column=1, padx=5, pady=5, sticky="e")
        self.BTN_kalibraceStart.grid(row=6, column=2, padx=5, pady=5, sticky="w")
    
    def je_int(self, vstup):
        if vstup in (""):
            return True
        try:
            int(vstup)
            return True
        except ValueError:
            return False
    
    def je_float(self, vstup):
        if vstup in (""):
            return True
        try:
            float(vstup)
            return True
        except ValueError:
            return False
    
    def okno_kalibrace(self):
        if (self.controller.piezo == True) and (self.controller.mcu == True):    
            self.BTN_kalibraceStart.config(state="disabled")
            print(f"[KalibraceGUI] vytvoreni okna noveho")
            self.okno_nove_kalibrace = KalibracniOkno(self.controller.view.root, self, self.controller)
        else:
            InfoMsg = f"CHYBA\nNesplněny podmínky zapnutí kalibrace"
            messagebox.showinfo("Chyba", InfoMsg)

#------------------------------        
#DATA PAGE 
#VYTVORENI VYHODNOCENI NAMERENYCH DAT
#------------------------------           
class DataPage(ScrollableFrame):
    def __init__(self, parent, controller : 'MainController'):
        super().__init__(parent)
        self.config(bg="white")
        
        self.data : LabelFrame = DataGUI(self.scrollable_frame, controller)
        self.data.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        
        self.razitko : LabelFrame = RazitkoGUI(self.scrollable_frame, controller)
        self.razitko.grid(row=0, column=1, padx=5, pady=5, sticky="nw")
        
        self.informace_kalibrace : LabelFrame = InformaceKalibraceGUI(self.scrollable_frame, controller)
        self.informace_kalibrace.grid(row=0, column=2, padx=5, pady=5, sticky="nw")
        
        self.okolni_podminky : LabelFrame = OkolniPodminkyGUI(self.scrollable_frame, controller)
        self.okolni_podminky.grid(row=0, column=3, padx=5, pady=5, sticky="nw")
                        
        self.excel_start : LabelFrame = ExcelGUI(self.scrollable_frame, controller)
        self.excel_start.grid(row=0, column=4, padx=5, pady=5, sticky="nw")
        
        self.controler = controller
        self.controler.set_data_page(self)                
                  
class DataGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController'):
        super().__init__(parent, text="Data kalibrace", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        
        #button pro data z posledniho mereni
        self.BTN_posledni_mereni_data = Button(self, text="Poslední kalibrace", width=18, state="active", command= lambda: self.controller.M_C_posledni_kalibrace_nahrat_data())
        self.BTN_posledni_mereni_data.grid(row=0, column=0, padx=5, pady=5, sticky="NE")
        
        self.BTN_soubor_mereni_data = Button(self, text="Data ze souboru", width=18, state="active", command= lambda:1)
        self.BTN_soubor_mereni_data.grid(row=1, column=0, padx=5, pady=5, sticky="NE")
                  
class RazitkoGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController'):
        super().__init__(parent, text="Razítko", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        
        #RAZITKO label
        sirka_label = 15
        self.label_nazev = Label(self, text="Název", bg="white", width=sirka_label, anchor="e")
        self.label_katedra = Label(self, text="Katedra", bg="white", width=sirka_label, anchor="e")
        self.label_technicka_reference = Label(self, text="Technická reference", bg="white", width=sirka_label, anchor="e")
        self.label_kalibroval = Label(self, text="Kalibroval", bg="white", width=sirka_label, anchor="e")
        self.label_schvalil = Label(self, text="Schválil", bg="white", width=sirka_label, anchor="e")
        self.label_projekt = Label(self, text="Projekt", bg="white", width=sirka_label, anchor="e")
        self.label_status_dokumentu = Label(self, text="Status dokumentu", bg="white",width=sirka_label, anchor="e")
        self.label_cislo_dokumentu = Label(self, text="Číslo dokumentu", bg="white", width=sirka_label, anchor="e")
        self.label_univerzita = Label(self, text="Univerzita", bg="white", width=sirka_label, anchor="e")
        self.label_revize = Label(self, text="Revize", bg="white", width=sirka_label, anchor="e")
        self.label_datum = Label(self, text="Datum", bg="white", width=sirka_label, anchor="e")
        self.label_jazyk = Label(self, text="Jazyk", bg="white", width=sirka_label, anchor="e")
        
        #RAZITKO Entry
        sirka_entry = 20
        self.entry_nazev = Entry(self, width=sirka_entry)
        self.entry_katedra = Entry(self, width=sirka_entry)
        self.entry_katedra.insert(0, "352") #DEFAULTNE 352
        self.entry_technicka_reference = Entry(self, width=sirka_entry)
        self.entry_kalibroval = Entry(self, width=sirka_entry)
        self.entry_schvalil = Entry(self, width=sirka_entry)
        self.entry_projekt = Entry(self, width=sirka_entry)
        self.entry_status_dokumentu = Entry(self, width=sirka_entry)
        self.entry_status_dokumentu.insert(0,"uvolněno")
        self.entry_cislo_dokumentu = Entry(self, width=sirka_entry)
        self.entry_univerzita = Entry(self, width=sirka_entry)
        self.entry_univerzita.insert(0, "VŠB-TUO")
        self.entry_revize = Entry(self, width=sirka_entry)
        self.entry_revize.insert(0, "AA")
        self.entry_datum = Entry(self, width=sirka_entry)
        self.entry_datum.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.entry_jazyk = Entry(self, width=sirka_entry)
        self.entry_jazyk.insert(0, "cs")
        
        #RAZITKO grid
        self.label_nazev.grid(row=0, column=0, padx=5, pady=5, sticky="NE")
        self.entry_nazev.grid(row=0, column=1, padx=5, pady=5,sticky="NE")
        self.label_katedra.grid(row=1, column=0, padx=5, pady=5, sticky="NE")
        self.entry_katedra.grid(row=1, column=1, padx=5, pady=5,sticky="NE")
        self.label_technicka_reference.grid(row=2, column=0, padx=5, pady=5, sticky="NE")
        self.entry_technicka_reference.grid(row=2, column=1, padx=5, pady=5, sticky="NE")
        self.label_kalibroval.grid(row=3, column=0, padx=5, pady=5, sticky="NE")
        self.entry_kalibroval.grid(row=3, column=1, padx=5, pady=5, sticky="NE")
        self.label_schvalil.grid(row=4, column=0, padx=5, pady=5, sticky="NE")
        self.entry_schvalil.grid(row=4, column=1, padx=5, pady=5, sticky="NE")
        self.label_projekt.grid(row=5, column=0, padx=5, pady=5, sticky="NE")
        self.entry_projekt.grid(row=5, column=1, padx=5, pady=5, sticky="NE")
        self.label_status_dokumentu.grid(row=6, column=0, padx=5, pady=5, sticky="NE")
        self.entry_status_dokumentu.grid(row=6, column=1, padx=5, pady=5, sticky="NE")
        self.label_cislo_dokumentu.grid(row=7, column=0, padx=5, pady=5, sticky="NE")
        self.entry_cislo_dokumentu.grid(row=7, column=1, padx=5, pady=5, sticky="NE")
        self.label_univerzita.grid(row=8, column=0, padx=5, pady=5, sticky="NE")
        self.entry_univerzita.grid(row=8, column=1, padx=5, pady=5, sticky="NE")
        self.label_revize.grid(row=9, column=0, padx=5, pady=5, sticky="NE")
        self.entry_revize.grid(row=9, column=1, padx=5, pady=5, sticky="NE")
        self.label_datum.grid(row=10, column=0, padx=5, pady=5, sticky="NE")
        self.entry_datum.grid(row=10, column=1, padx=5, pady=5, sticky="NE")
        self.label_jazyk.grid(row=11, column=0, padx=5, pady=5, sticky="NE")
        self.entry_jazyk.grid(row=11, column=1, padx=5, pady=5, sticky="NE")

class InformaceKalibraceGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController'):
        super().__init__(parent, text="Informace o kalibraci", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        
        #Informace o kalibraci label
        sirka_label = 15
        self.label_typ_snimace = Label(self, text="Typ snímače", bg="white", width=sirka_label, anchor="e")
        self.label_snimany_objekt = Label(self, text="Snímaný objekt", bg="white", width=sirka_label, anchor="e")
        self.label_snimany_material = Label(self, text="Snímaný materiál", bg="white", width=sirka_label, anchor="e")
        self.label_obvod_zpracovani = Label(self, text="Obvod zpracování", bg="white", width=sirka_label, anchor="e")
        self.label_napajeni = Label(self, text="Napájení", bg="white", width=sirka_label, anchor="e")
        
        #Informace o kalibraci entry
        sirka_entry = 20
        self.entry_typ_snimace = Entry(self, width=sirka_entry)
        self.entry_snimany_objekt = Entry(self, width=sirka_entry)
        self.entry_snimany_material = Entry(self, width=sirka_entry)
        self.entry_obvod_zpracovani = Entry(self, width=sirka_entry)
        self.entry_napajeni = Entry(self, width=sirka_entry)
        
        #Infromace o kalibraci grid
        self.label_typ_snimace.grid(row=0, column=0, padx=5, pady=5, sticky="NE")
        self.entry_typ_snimace.grid(row=0, column=1, padx=5, pady=5,sticky="NE")
        self.label_snimany_objekt.grid(row=1, column=0, padx=5, pady=5, sticky="NE")
        self.entry_snimany_objekt.grid(row=1, column=1, padx=5, pady=5, sticky="NE")
        self.label_snimany_material.grid(row=2, column=0, padx=5, pady=5, sticky="NE")
        self.entry_snimany_material.grid(row=2, column=1, padx=5, pady=5, sticky="NE")
        self.label_obvod_zpracovani.grid(row=3, column=0, padx=5, pady=5, sticky="NE")
        self.entry_obvod_zpracovani.grid(row=3, column=1, padx=5, pady=5, sticky="NE")
        self.label_napajeni.grid(row=4, column=0, padx=5, pady=5, sticky="NE")
        self.entry_napajeni.grid(row=4, column=1, padx=5, pady=5, sticky="NE")
        
class OkolniPodminkyGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController'):
        super().__init__(parent, text="Okolní podmínky", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        
        #Informace o podminkach label
        sirka_label = 15
        self.label_teplota = Label(self, text="Teplota (°C)", bg="white", width=sirka_label, anchor="e")
        self.label_tlak = Label(self, text="Tlak (Pa)", bg="white", width=sirka_label, anchor="e")
        self.label_vlhkost = Label(self, text="Vlhkost (%)", bg="white", width=sirka_label, anchor="e")
        self.label_osvetleni = Label(self, text="Osvětlení (lux)", bg="white", width=sirka_label, anchor="e")
        
        #Informace o podminkach entry
        sirka_entry = 20
        self.entry_teplota = Entry(self, width=sirka_entry)
        self.entry_tlak = Entry(self, width=sirka_entry)
        self.entry_vlhkost = Entry(self, width=sirka_entry)
        self.entry_osvetleni = Entry(self, width=sirka_entry)
        
        #informace o podminkach grid
        self.label_teplota.grid(row=0, column=0, padx=5, pady=5, sticky="NE")
        self.entry_teplota.grid(row=0, column=1, padx=5, pady=5,sticky="NE")
        self.label_tlak.grid(row=1, column=0, padx=5, pady=5, sticky="NE")
        self.entry_tlak.grid(row=1, column=1, padx=5, pady=5, sticky="NE")
        self.label_vlhkost.grid(row=2, column=0, padx=5, pady=5, sticky="NE")
        self.entry_vlhkost.grid(row=2, column=1, padx=5, pady=5, sticky="NE")
        self.label_osvetleni.grid(row=3, column=0, padx=5, pady=5, sticky="NE")
        self.entry_osvetleni.grid(row=3, column=1, padx=5, pady=5, sticky="NE")
        
class ExcelGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController'):
        super().__init__(parent, text="Excel", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        
        self.BTN_excelstart = Button(self, text="Excel start", width=18, state="active", command= lambda: self.controller.M_C_excel_start())
        self.BTN_excelstart.grid(row=0, column=0, padx=5, pady=5, sticky="NE") 
        

#TRIDA PRO SPRAVOVANI KALIBRACNICH KRIVEK        
class KalibracniKrivkyPage(ScrollableFrame):
    def __init__(self, parent, controller : 'MainController'):
        super().__init__(parent)
        self.config(bg="white")
        self.controler = controller
        self.original_data_instance = []
        self.instance_pocet = 0
        self.original_data_pocet : LabelFrame = OriginalDataPocet(self.scrollable_frame, self.controler)
        self.original_data_pocet.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        
        self.update_data(1)           
        self.controler.set_KalibracniKrivky_page(self)
        
    def update_data(self, inkrement):
        if not (1 <= self.instance_pocet + inkrement <= 10):
            return
        
        self.instance_pocet = self.instance_pocet + (inkrement)
        
        #pridani
        if inkrement == 1:
            idx = len(self.original_data_instance) 
            instance = OriginalDataGUI(self.scrollable_frame, self.controler, idx)
            instance.grid(row=idx + 1, column=0, padx=5, pady=5, sticky="nw")
            self.original_data_instance.append(instance) #sem se ukladaji instance OriginalDataGUI

        #odebrani
        elif inkrement == -1:
            if not self.original_data_instance:
                return
            last = self.original_data_instance.pop()
            last.destroy()

            for i, inst in enumerate(self.original_data_instance):
                inst.poradi_instance = i
                inst.grid(row=i + 1, column=0, padx=5, pady=5, sticky="nw")

        self.instance_pocet = len(self.original_data_instance)
        if self.instance_pocet == 0:
            self.instance_pocet = 0
        
class OriginalDataPocet(LabelFrame):
    def __init__(self, parent, controller : 'MainController'):
        super().__init__(parent, text="Přidat data", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        self.label_data_pocet = Label(self, text="Křivky (max 10)", bg="white", width=20, anchor="w")

        self.BTN_original_data_pridat = Button(self, text="+", width=8, state="active", command=lambda: self.controller.M_C_zmena_poctu_OriginalData(1))
        self.BTN_original_data_odebrat = Button(self, text="-", width=8, state="active", command=lambda: self.controller.M_C_zmena_poctu_OriginalData(-1))
        self.publish()
        
    def publish(self):
        self.label_data_pocet.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        self.BTN_original_data_pridat.grid(row=0, column=1, padx=5, pady=5, sticky="nw")
        self.BTN_original_data_odebrat.grid(row=0, column=2, padx=5, pady=5, sticky="nw")
        
#frame originalni data
class OriginalDataGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController', poradi_instance):
        super().__init__(parent, text="Data", padx=5, pady=5, bg="white",bd=5, relief="groove")
        self.controller = controller
        self.poradi_instance = poradi_instance
        self.data = KalibracniKrivkyData(controller=self.controller)
        self.frame_popisky = Frame(self, bg="white")
        self.label_soubor = Label(self.frame_popisky, text="Pracovní soubor:", bg="white", width=20, anchor="w")
        self.Entry_pracovni_soubor = Entry(self.frame_popisky, width=30, state="normal")
        self.Entry_pracovni_soubor.insert(0, "N/A")
        self.Entry_pracovni_soubor.config(state="readonly")
        self.BTN_pracovni_soubor = Button(self.frame_popisky, text="SOUBOR", width=18, state="active", command= lambda: self.controller.M_C_vybrat_pracovni_soubor(self.poradi_instance))
        self.soubor_vybrany = False
        
        #oblast pro graf
        self.frame_graf = Frame(self, bg="white")    
        self.label_otevrit = Label(self.frame_popisky, text="Vykreslit data:", bg="white", width=20, anchor="w")
        self.BTN_otevrit = Button(self.frame_popisky, text="VYKRESLIT", width=18, state="active", command = lambda: self.controller.M_C_vykresli_graf(self.poradi_instance))     
        
        #oblast pro filtraci
        self.frame_filtrace = FiltraceDatGUI(self, controller=self.controller, poradi_instance=self.poradi_instance)
        self.frame_graf2 = Frame(self, bg="white") 
        
        #oblast pro lookup tabulku
        self.frame_lookuptable = LookupTabulkaGUI(self, controller=self.controller, poradi_instance=self.poradi_instance)
        
        
        self.publish()
        
    def publish(self):
        self.frame_popisky.grid(row=0, column=0, pady=5, sticky="nw")
        self.label_soubor.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        self.Entry_pracovni_soubor.grid(row=0, column=1, padx=5, pady=5, sticky="nw")
        self.BTN_pracovni_soubor.grid(row=0, column=2, padx=5, pady=5, sticky="nw")
        self.frame_graf.grid(row=0, column=1, padx=0, pady=0, sticky="nw")  
        self.label_otevrit.grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.BTN_otevrit.grid(row=1, column=1, padx=5, pady=5, sticky="nw")
        self.frame_filtrace.grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.frame_graf2.grid(row=1, column=1, padx=0, pady=0, sticky="nw")         
        self.frame_lookuptable.grid(row=2, column=0, padx=5, pady=5, sticky="nw")
    
    def graf(self):
        if not hasattr(self, 'canvas'):
            self.fig, (self.ax1, self.ax2, self.ax3, self.ax4, self.ax5) = plt.subplots(1, 5, figsize=(30,5))
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graf)
            self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
            self.fig.subplots_adjust(left=0.05, right=0.95, wspace=0.3)
            
        self.ax1.clear()
        self.ax1.grid(True, which='both', linestyle='--', alpha=0.5)
        self.ax1.set_title(f"Závislost {self.data.data_typ} na přiblížení stěny (reference) ke snímači")
        self.ax1.set_xlabel("Vzdálenost (um)")
        self.ax1.set_ylabel(f"{self.data.data_typ} {self.data.data_jednotka}")
        self.ax1.minorticks_on()
        # self.ax1.step(self.data.data_x, self.data.data_y, where = 'post', color='red')
        self.ax1.plot(self.data.data_x, self.data.data_y, 'o', markersize=1, color='red')
        
        self.ax2.clear()
        self.ax2.grid(True, which='both', linestyle='--', alpha=0.5)
        self.ax2.set_title("Průběh teploty")
        self.ax2.set_xlabel("Čas t(s)")
        self.ax2.set_ylabel("Teplota (°C)")
        self.ax2.step(self.data.data_cas, self.data.data_teplota, where = 'post', color='red')
        y2 = self.data.data_teplota
        y_min2 = min(y2)
        y_max2 = max(y2)
        rozsah2 = y_max2 - y_min2
        self.ax2.set_ylim(y_min2 -  5 * rozsah2, y_max2 +  5 * rozsah2)
        # self.ax2.plot(self.data.data_cas, self.data.data_teplota, 'o', markersize=1, color='red')
        
        self.ax3.clear()
        self.ax3.grid(True, which='both', linestyle='--', alpha=0.5)
        self.ax3.set_title("Průběh tlaku")
        self.ax3.set_xlabel("Čas t(s)")
        self.ax3.set_ylabel("Tlak (Pa)")
        self.ax3.step(self.data.data_cas, self.data.data_tlak, where = 'post', color='red')
        y3 = self.data.data_tlak
        y_min3 = min(y3)
        y_max3 = max(y3)
        rozsah3 = y_max3 - y_min3
        self.ax3.set_ylim(y_min3 - 5 * rozsah3, y_max3 + 5 * rozsah3)
        # self.ax3.plot(self.data.data_cas, self.data.data_tlak, 'o', markersize=1, color='red')
        
        self.ax4.clear()
        self.ax4.grid(True, which='both', linestyle='--', alpha=0.5)
        self.ax4.set_title("Průběh vlhkosti")
        self.ax4.set_xlabel("Čas t(s)")
        self.ax4.set_ylabel("Vlhkost (%)")
        self.ax4.step(self.data.data_cas, self.data.data_vlhkost, where = 'post', color='red')
        self.ax4.set_ylim(0, 100)
        # self.ax4.plot(self.data.data_cas, self.data.data_vlhkost, 'o', markersize=1, color='red')
        
        self.ax5.clear()
        self.ax5.grid(True, which='both', linestyle='--', alpha=0.5)
        self.ax5.set_title("Průběh osvětlení")
        self.ax5.set_xlabel("Čas t(s)")
        self.ax5.set_ylabel("Osvětlení (lux)")
        self.ax5.step(self.data.data_cas, self.data.data_osvetleni, where = 'post', color='red')
        y5 = self.data.data_osvetleni
        y_min5 = min(y5)
        y_max5 = max(y5)
        rozsah5 = y_max5 - y_min5
        self.ax5.set_ylim(y_min5 - 5 * rozsah5, y_max5 + 5 * rozsah5)
        # self.ax5.plot(self.data.data_cas, self.data.data_osvetleni, 'o', markersize=1, color='red')

        self.canvas.draw()
        
    def graf_filtrovany(self):
        if not hasattr(self, 'canvas_filtrace'):
            self.fig_filtrace, self.ax_filtrace = plt.subplots(figsize=(12,5))
            self.canvas_filtrace = FigureCanvasTkAgg(self.fig_filtrace, master=self.frame_graf2)

            widget = self.canvas_filtrace.get_tk_widget()
            widget.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.ax_filtrace.clear()
        self.ax_filtrace.set_title(f"(Filtrace) závislosti {self.data.data_typ} na přiblížení stěny (reference) ke snímači - {self.frame_filtrace.vybrana_filtrace.get()}")
        self.ax_filtrace.set_xlabel("Vzdálenost (um)")
        self.ax_filtrace.set_ylabel(f"{self.data.data_typ} {self.data.data_jednotka}")
        self.ax_filtrace.grid(True, which='both', linestyle='--', alpha=0.5)
        self.ax_filtrace.plot(self.data.osa_filtrovane,self.data.data_filtrovane,linestyle = 'solid', color='red', label="Filtrované data")
        self.ax_filtrace.plot(self.data.data_x,self.data.data_y, 'o', markersize=0.1, color="#828486", label = "Originální data")
        self.ax_filtrace.legend()
        self.fig_filtrace.subplots_adjust(left=0.18, right=0.95, top=0.9, bottom=0.15)
        self.ax_filtrace.yaxis.labelpad = 20
        
        #KURZOR
        if hasattr(self, 'cursor_filtrace'):
            self.cursor_filtrace.disconnect()
            del self.cursor_filtrace
        cursor = mplcursors.cursor(self.ax_filtrace, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(f"x = {sel.target[0]:.3f}\ny = {sel.target[1]:.3f}"))
        self.canvas_filtrace.draw()

#frame filtrace dat
class FiltraceDatGUI(LabelFrame):
    def __init__(self, parent, controller : 'MainController', poradi_instance):
        super().__init__(parent, text='Filtrace dat', padx=5, pady=5, bg="white", bd=5, relief="groove")
        self.controller = controller
        self.poradi_instance = poradi_instance
        self.frame_popisky = Frame(self, bg="white")
        #Pokud byla vybrana pracovni slozka, tak se automaticky vybere stejna pro filtraci - lze zmenit dale
        self.metody_filtrace = ["Průměr", "Medián", "MA", "EMA", "S-G","Průměr+EMA", "Průměr+EMA+S-G"]
        self.label_metoda_filtrace = Label(self.frame_popisky, text="Metoda filtrace :", bg="white", width=20, anchor="w")
        self.vybrana_filtrace = StringVar()
        self.vybrana_filtrace.set("-")
        self.drop_filtrace = OptionMenu(self.frame_popisky, self.vybrana_filtrace, *self.metody_filtrace)
        self.drop_filtrace.config(width=18)
        self.BTN_filtrace = Button(self.frame_popisky, text="FILTRACE", width=18, state="active", command=lambda: self.BTN_filtrace_prikaz())
    
        self.publish()
        
    def publish(self):
        self.frame_popisky.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        self.label_metoda_filtrace.grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.drop_filtrace.grid(row=1, column=1, padx=5, pady=5, sticky="nw")
        self.BTN_filtrace.grid(row=1, column=2, padx=5, pady=5, sticky="nw")
        
    def je_int(self, vstup):
        if vstup in (""):
            return True
        try:
            int(vstup)
            return True
        except ValueError:
            return False
    
    def je_float(self, vstup):
        if vstup in (""):
            return True
        try:
            float(vstup)
            return True
        except ValueError:
            return False
        
    def BTN_filtrace_prikaz(self):
        self.controller.filtrace_zapnuta = True
        
        self.controller.M_C_vykresli_graf_filtrace(self.poradi_instance, self.vybrana_filtrace.get())
        validace_float = (self.controller.root.register(self.je_float), "%P") 
        validace_int = (self.controller.root.register(self.je_int), "%P")


        for widget in self.frame_popisky.winfo_children():
            info = widget.grid_info()
            if info and int(info.get("row", 0)) >= 2:
                widget.grid_forget()


        if self.vybrana_filtrace.get() == "Průměr+EMA":
            self.label_alphaEMA = Label(self.frame_popisky, text="Alfa exponenciálního filtru:", bg="white", width=20, anchor="w")
            self.entry_filtr_EMA = Entry(self.frame_popisky, width=20, state="normal", validate="key", validatecommand=validace_float)
            self.entry_filtr_EMA.bind("<Return>", lambda _: self.controller.M_C_vykresli_graf_filtrace(
                self.poradi_instance,
                self.vybrana_filtrace.get(),
                filtr_EMA=self.entry_filtr_EMA.get()))

            self.BTN_filtr = Button(self.frame_popisky, text="Aktualizace", width=18, command=lambda: self.controller.M_C_vykresli_graf_filtrace(
                self.poradi_instance,
                self.vybrana_filtrace.get(),
                filtr_EMA=self.entry_filtr_EMA.get()))

            self.label_alphaEMA.grid(row=2, column=0, padx=5, pady=5, sticky="nw")
            self.entry_filtr_EMA.grid(row=2, column=1, padx=5, pady=5, sticky="nw")
            self.BTN_filtr.grid(row=2, column=2, padx=5, pady=5, sticky="nw")

        elif self.vybrana_filtrace.get() == "Průměr+EMA+S-G":
            self.label_alphaEMA = Label(self.frame_popisky, text="Alfa exponenciálního filtru:", bg="white", width=20, anchor="w")
            self.label_filtr_SG = Label(self.frame_popisky, text="Okno Savgol-Gola filtru:", bg="white", width=20, anchor="w")
            self.label_exponent_SG = Label(self.frame_popisky, text="Exponent Savgol-Gola filtru:", bg="white", width=20, anchor="w")

            self.entry_filtr_EMA = Entry(self.frame_popisky, width=30, state="normal", validate="key", validatecommand=validace_float)
            self.entry_filtr_SG = Entry(self.frame_popisky, width=30, state="normal", validate="key", validatecommand=validace_float)
            self.entry_exponent_SG = Entry(self.frame_popisky, width=30, state="normal", validate="key", validatecommand=validace_int)

            for entry in [self.entry_filtr_EMA, self.entry_filtr_SG, self.entry_exponent_SG]:
                entry.bind("<Return>", lambda _: self.controller.M_C_vykresli_graf_filtrace(
                    self.poradi_instance,
                    self.vybrana_filtrace.get(),
                    filtr_EMA=self.entry_filtr_EMA.get(),
                    filtr_SG=self.entry_filtr_SG.get(),
                    exponent_SG=self.entry_exponent_SG.get()))

            self.BTN_filtr = Button(self.frame_popisky, text="Aktualizace", width=18, command=lambda: self.controller.M_C_vykresli_graf_filtrace(
                self.poradi_instance,
                self.vybrana_filtrace.get(),
                filtr_EMA=self.entry_filtr_EMA.get(),
                filtr_SG=self.entry_filtr_SG.get(),
                exponent_SG=self.entry_exponent_SG.get()))

            self.label_alphaEMA.grid(row=2, column=0, padx=5, pady=5, sticky="nw")
            self.entry_filtr_EMA.grid(row=2, column=1, padx=5, pady=5, sticky="nw")
            self.label_filtr_SG.grid(row=3, column=0, padx=5, pady=5, sticky="nw")
            self.entry_filtr_SG.grid(row=3, column=1, padx=5, pady=5, sticky="nw")
            self.label_exponent_SG.grid(row=4, column=0, padx=5, pady=5, sticky="nw")
            self.entry_exponent_SG.grid(row=4, column=1, padx=5, pady=5, sticky="nw")
            self.BTN_filtr.grid(row=2, column=2, padx=5, pady=5, sticky="nw")
            
            
class LookupTabulkaGUI(LabelFrame):
    
    
        
            