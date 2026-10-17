from __future__ import annotations
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import requests

BASE = Path(__file__).resolve().parent
PATH = BASE / "config" / "smart_home.json"

DEFAULT = {
    "home_assistant": {"url": "", "token": "", "verify_ssl": True},
    "ewelink": {"url": "", "token": "", "verify_ssl": True},
    "tuya": {"devices": []},
}


def load():
    if PATH.exists():
        try:
            data = json.loads(PATH.read_text(encoding="utf-8"))
            for k, v in DEFAULT.items():
                data.setdefault(k, v.copy() if isinstance(v, dict) else v)
            return data
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT))


def save(data):
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS BR — Casa Inteligente")
        self.geometry("760x620")
        self.minsize(700, 560)
        self.data = load()

        title = ttk.Label(self, text="JARVIS — AUTOMAÇÃO RESIDENCIAL", font=("Segoe UI", 18, "bold"))
        title.pack(pady=(18, 6))
        ttk.Label(self, text="Integre Home Assistant, eWeLink CUBE/iHost e Smart Life/Tuya.").pack()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=16)

        self.ha_tab = ttk.Frame(nb)
        self.ew_tab = ttk.Frame(nb)
        self.tuya_tab = ttk.Frame(nb)
        nb.add(self.ha_tab, text="Home Assistant")
        nb.add(self.ew_tab, text="eWeLink")
        nb.add(self.tuya_tab, text="Smart Life / Tuya")

        self._build_ha()
        self._build_ewelink()
        self._build_tuya()

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Button(bottom, text="SALVAR TUDO", command=self.save_all).pack(side="right")

    def _row(self, parent, label, value="", secret=False):
        f = ttk.Frame(parent)
        f.pack(fill="x", padx=16, pady=8)
        ttk.Label(f, text=label, width=28).pack(side="left")
        var = tk.StringVar(value=value)
        e = ttk.Entry(f, textvariable=var, show="*" if secret else "")
        e.pack(side="left", fill="x", expand=True)
        return var

    def _build_ha(self):
        ttk.Label(self.ha_tab, text="Home Assistant (API REST)", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16,4))
        ttk.Label(self.ha_tab, text="Use a URL como http://192.168.1.50:8123 e um Long-Lived Access Token.").pack(anchor="w", padx=16)
        cfg = self.data["home_assistant"]
        self.ha_url = self._row(self.ha_tab, "URL do Home Assistant", cfg.get("url",""))
        self.ha_token = self._row(self.ha_tab, "Token de acesso", cfg.get("token",""), True)
        ttk.Button(self.ha_tab, text="TESTAR CONEXÃO", command=self.test_ha).pack(pady=14)

    def _build_ewelink(self):
        ttk.Label(self.ew_tab, text="eWeLink CUBE / iHost (Open API V2 local)", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16,4))
        ttk.Label(self.ew_tab, text="Para eWeLink Cloud comum, use o Home Assistant como ponte. Para iHost/CUBE, use os campos abaixo.").pack(anchor="w", padx=16)
        cfg = self.data["ewelink"]
        self.ew_url = self._row(self.ew_tab, "IP/URL do iHost/CUBE", cfg.get("url",""))
        self.ew_token = self._row(self.ew_tab, "Token Open API", cfg.get("token",""), True)
        ttk.Button(self.ew_tab, text="TESTAR CONEXÃO", command=self.test_ewelink).pack(pady=14)

    def _build_tuya(self):
        ttk.Label(self.tuya_tab, text="Smart Life / Tuya — controle local", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16,4))
        ttk.Label(self.tuya_tab, text="Adicione os dispositivos com ID, IP e Local Key. As chaves ficam somente neste PC.").pack(anchor="w", padx=16)
        self.listbox = tk.Listbox(self.tuya_tab, height=12)
        self.listbox.pack(fill="both", expand=True, padx=16, pady=12)
        self.refresh_tuya()
        f = ttk.Frame(self.tuya_tab)
        f.pack(fill="x", padx=16, pady=(0,16))
        ttk.Button(f, text="ADICIONAR", command=self.add_tuya).pack(side="left")
        ttk.Button(f, text="REMOVER", command=self.remove_tuya).pack(side="left", padx=8)
        ttk.Button(f, text="TESTAR SELECIONADO", command=self.test_tuya).pack(side="right")

    def refresh_tuya(self):
        self.listbox.delete(0, tk.END)
        for d in self.data["tuya"].get("devices", []):
            self.listbox.insert(tk.END, f"{d.get('name')} — {d.get('ip')} — {d.get('type','switch')}")

    def add_tuya(self):
        name = simpledialog.askstring("Nome", "Nome do dispositivo (ex.: Luz da sala):", parent=self)
        if not name: return
        did = simpledialog.askstring("Device ID", "Device ID do Smart Life/Tuya:", parent=self)
        if not did: return
        ip = simpledialog.askstring("IP", "IP local do dispositivo:", parent=self)
        if not ip: return
        key = simpledialog.askstring("Local Key", "Local Key:", show="*", parent=self)
        if not key: return
        typ = simpledialog.askstring("Tipo", "Tipo: switch ou light", initialvalue="switch", parent=self) or "switch"
        ver = simpledialog.askstring("Versão", "Versão do protocolo (ex.: 3.3 ou 3.4)", initialvalue="3.3", parent=self) or "3.3"
        self.data["tuya"].setdefault("devices", []).append({
            "name": name, "id": did, "ip": ip, "local_key": key,
            "type": typ, "version": float(ver)
        })
        self.refresh_tuya()

    def remove_tuya(self):
        sel = self.listbox.curselection()
        if not sel: return
        self.data["tuya"]["devices"].pop(sel[0])
        self.refresh_tuya()

    def test_ha(self):
        try:
            url = self.ha_url.get().strip().rstrip("/")
            token = self.ha_token.get().strip()
            r = requests.get(f"{url}/api/", headers={"Authorization":f"Bearer {token}"}, timeout=5)
            r.raise_for_status()
            messagebox.showinfo("Sucesso", "Home Assistant conectado.")
        except Exception as e:
            messagebox.showerror("Falha", str(e))

    def test_ewelink(self):
        try:
            url = self.ew_url.get().strip().rstrip("/")
            token = self.ew_token.get().strip()
            r = requests.get(f"{url}/open-api/v2/rest/devices",
                             headers={"Authorization":f"Bearer {token}", "Content-Type":"application/json"},
                             timeout=5)
            r.raise_for_status()
            data = r.json()
            if data.get("error") not in (0, None):
                raise RuntimeError(data.get("message") or "Erro do eWeLink")
            count = len(((data.get("data") or {}).get("device_list") or []))
            messagebox.showinfo("Sucesso", f"eWeLink conectado. {count} dispositivo(s) encontrado(s).")
        except Exception as e:
            messagebox.showerror("Falha", str(e))

    def test_tuya(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selecione", "Selecione um dispositivo.")
            return
        d = self.data["tuya"]["devices"][sel[0]]
        try:
            import tinytuya
            cls = tinytuya.BulbDevice if str(d.get("type","")).lower() == "light" else tinytuya.OutletDevice
            dev = cls(d["id"], d["ip"], d["local_key"])
            dev.set_version(float(d.get("version", 3.3)))
            st = dev.status()
            messagebox.showinfo("Sucesso", f"Dispositivo respondeu:\n{st}")
        except Exception as e:
            messagebox.showerror("Falha", str(e))

    def save_all(self):
        self.data["home_assistant"]["url"] = self.ha_url.get().strip()
        self.data["home_assistant"]["token"] = self.ha_token.get().strip()
        self.data["ewelink"]["url"] = self.ew_url.get().strip()
        self.data["ewelink"]["token"] = self.ew_token.get().strip()
        save(self.data)
        messagebox.showinfo("Salvo", "Configurações da Casa Inteligente salvas neste PC.")


if __name__ == "__main__":
    App().mainloop()
