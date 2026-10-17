from __future__ import annotations
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

ROOT = Path(__file__).resolve().parent
LOC = ROOT / "config" / "location.json"
UX = ROOT / "config" / "ux.json"

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default.copy()

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS — Recursos")
        self.geometry("700x560")
        self.resizable(False,False)

        loc=load(LOC,{"enabled":False,"mode":"auto","manual_city":"","manual_region":""})
        ux=load(UX,{"clap_wake":True,"name_wake":True,"face":"nebula","neon_multicolor":True})

        ttk.Label(self,text="RECURSOS DO JARVIS",font=("Segoe UI",18,"bold")).pack(pady=(18,4))
        nb=ttk.Notebook(self)
        nb.pack(fill="both",expand=True,padx=16,pady=16)

        p1=ttk.Frame(nb); nb.add(p1,text="Localização")
        self.loc_enabled=tk.BooleanVar(value=loc.get("enabled",False))
        ttk.Checkbutton(p1,text="Ativar localização",variable=self.loc_enabled).pack(anchor="w",padx=18,pady=(16,8))
        self.loc_mode=tk.StringVar(value=loc.get("mode","auto"))
        ttk.Label(p1,text="Modo").pack(anchor="w",padx=18)
        ttk.Combobox(p1,textvariable=self.loc_mode,values=["auto","windows","approximate","manual"],state="readonly").pack(fill="x",padx=18,pady=6)
        self.city=tk.StringVar(value=loc.get("manual_city",""))
        self.region=tk.StringVar(value=loc.get("manual_region",""))
        ttk.Entry(p1,textvariable=self.city).pack(fill="x",padx=18,pady=6)
        ttk.Label(p1,text="Cidade manual").pack(anchor="w",padx=18)
        ttk.Entry(p1,textvariable=self.region).pack(fill="x",padx=18,pady=6)
        ttk.Label(p1,text="Estado/região manual").pack(anchor="w",padx=18)
        ttk.Button(p1,text="TESTAR LOCALIZAÇÃO",command=self.test_location).pack(pady=14)

        p2=ttk.Frame(nb); nb.add(p2,text="Ativação")
        self.clap=tk.BooleanVar(value=ux.get("clap_wake",True))
        self.name=tk.BooleanVar(value=ux.get("name_wake",True))
        ttk.Checkbutton(p2,text="Acordar com 1 palma",variable=self.clap).pack(anchor="w",padx=18,pady=(20,8))
        ttk.Checkbutton(p2,text='Acordar ao ouvir "Jarvis"',variable=self.name).pack(anchor="w",padx=18,pady=8)

        p4=ttk.Frame(nb); nb.add(p4,text="Dispositivos")
        ttk.Label(
            p4,
            text="JARVIS Device Link",
            font=("Segoe UI",14,"bold")
        ).pack(anchor="w",padx=18,pady=(18,6))
        ttk.Label(
            p4,
            text="Prepara o Windows para conectar o futuro aplicativo Android na mesma rede.",
            wraplength=620
        ).pack(anchor="w",padx=18)
        ttk.Label(
            p4,
            text="No JARVIS, pressione F8 para abrir o código de pareamento.",
            wraplength=620
        ).pack(anchor="w",padx=18,pady=(12,6))

        p3=ttk.Frame(nb); nb.add(p3,text="Visual")
        self.face=tk.StringVar(value=ux.get("face","particle"))
        ttk.Label(p3,text="Cara do JARVIS").pack(anchor="w",padx=18,pady=(18,6))
        ttk.Combobox(p3,textvariable=self.face,values=["nebula","particle","reactor","orb","minimal"],state="readonly").pack(fill="x",padx=18)
        self.neon=tk.BooleanVar(value=ux.get("neon_multicolor",True))
        ttk.Checkbutton(p3,text="Usar cores neon diferentes por estado",variable=self.neon).pack(anchor="w",padx=18,pady=14)

        ttk.Button(self,text="SALVAR",command=self.save_all).pack(pady=(0,16))

    def test_location(self):
        save(LOC,{
            "enabled":self.loc_enabled.get(),
            "mode":self.loc_mode.get(),
            "manual_city":self.city.get().strip(),
            "manual_region":self.region.get().strip(),
        })
        try:
            from core.location_service import get_location
            result=get_location()
            messagebox.showinfo("Localização",f"Localização funcionando:\n{result}")
        except Exception as e:
            messagebox.showerror("Localização",str(e))

    def save_all(self):
        save(LOC,{
            "enabled":self.loc_enabled.get(),
            "mode":self.loc_mode.get(),
            "manual_city":self.city.get().strip(),
            "manual_region":self.region.get().strip(),
        })
        save(UX,{
            "clap_wake":self.clap.get(),
            "name_wake":self.name.get(),
            "face":self.face.get(),
            "neon_multicolor":self.neon.get(),
        })
        messagebox.showinfo("JARVIS","Configurações salvas.")
        self.destroy()

if __name__=="__main__":
    App().mainloop()
