from tkinter import filedialog
import numpy as np
 
class LUT_model():
    def __init__(self, controller):
            self.controller = controller
    
    
    def vytvorit_LUT(self, data_x, data_y, velikost_tabulky):
        
        N = velikost_tabulky
        rozdeleni = np.linspace(0, len(data_y)-1, N, dtype=int)

        x_lut = np.array(data_x)[rozdeleni]
        y_lut = np.array(data_y)[rozdeleni]
         
        cesta = filedialog.asksaveasfilename(
            title="Uložit lookup tabulku",
            defaultextension=".h",
            filetypes=[("C header file", "*.h")]
        )
        
        if not cesta:
            return
        
        self._uloz_lookup_do_h(cesta, x_lut, y_lut)
        
    def _uloz_lookup_do_h(self, cesta, x_lut, y_lut, scale=1):
        with open(cesta, "w", encoding="utf-8") as f:
            f.write("#ifndef LOOKUP_TABLE_H\n")
            f.write("#define LOOKUP_TABLE_H\n\n")
            f.write("#include <stdint.h>\n\n")
    
            f.write(f"#define LUT_SIZE {len(x_lut)}\n")
            f.write(f"#define LUT_SCALE {scale}\n\n")
    
            f.write("static const uint16_t lut_x[LUT_SIZE] = {\n")
            for val in x_lut:
                f.write(f"    {int(round(val * scale))},\n")
            f.write("};\n\n")
    
            f.write("static const uint32_t lut_y[LUT_SIZE] = {\n")
            for val in y_lut:
                f.write(f"    {int(round(val * scale))},\n")
            f.write("};\n\n")
    
            f.write("#endif // LOOKUP_TABLE_H\n")