"""Protótipo de desconexão visual do Core (requer sessão autenticada)."""
import re, time, threading, unicodedata
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui as pg
from rapidocr_onnxruntime import RapidOCR
pg.FAILSAFE=True
ocr=RapidOCR()
def norm(s):
    s=''.join(c for c in unicodedata.normalize('NFD',str(s).upper()) if unicodedata.category(c)!='Mn')
    return re.sub(r'[^A-Z0-9_]','',s)
def scan():
    shot=pg.screenshot()
    import numpy as np
    result,_=ocr(np.array(shot))
    items=[]
    for box,txt,score in (result or []):
        x=min(p[0] for p in box); y=min(p[1] for p in box)
        w=max(p[0] for p in box)-x; h=max(p[1] for p in box)-y
        if score>.4: items.append((norm(txt),x,y,w,h))
    return items
def center(t): return (int(t[1]+t[3]/2),int(t[2]+t[4]/2))
def find_session(items,user):
    online=[t for t in items if 'ONLINE' in t[0] and 'OFFLINE' not in t[0]]
    offline=[t for t in items if 'OFFLINE' in t[0]]
    if not online or not offline: raise RuntimeError('A lista não está visível ou não foi reconhecida. Deixe a janela do GO-Global com o Core na frente, maximizada, mostrando Usuários ON-LINE e OFF-LINE.')
    pairs=[(a,b) for a in online for b in offline if b[1]>a[1] and abs(b[2]-a[2])<65]
    if not pairs: raise RuntimeError('Não consegui identificar a área das sessões online.')
    a,b=min(pairs,key=lambda p:p[1][1]-p[0][1])
    found=[t for t in items if a[1]-40<=t[1]<=b[1]-3 and a[2]+10<t[2]<a[2]+510 and (t[0]==user or t[0].startswith(user+'_'))]
    if len(found)!=1: raise RuntimeError('Foram encontradas '+str(len(found))+' correspondências. Informe o identificador completo, se necessário.')
    return found[0]
def find_menu(items):
    # Menu somente após clique direito e com três palavras reconhecidas no mesmo alinhamento.
    for t in items:
        if t[0]!='DESCONECTAR': continue
        row=[p[0] for p in items if p[1]>=t[1] and abs(p[2]-t[2])<23]
        if 'SESSAO' in row and 'USUARIO' in row: return t
    raise RuntimeError('Não foi encontrado o comando Desconectar Sessão Usuário no menu.')
class App:
    def __init__(self):
        self.root=tk.Tk();self.root.title('BSOFT - Desconectar Sessão');self.root.geometry('400x205')
        self.user=tk.StringVar()
        f=ttk.Frame(self.root,padding=22);f.pack(fill='both',expand=True)
        ttk.Label(f,text='ID do usuário').pack(anchor='w')
        ttk.Entry(f,textvariable=self.user,font=('Segoe UI',16)).pack(fill='x',pady=9)
        self.btn=ttk.Button(f,text='Derrubar conexão',command=self.start);self.btn.pack(fill='x')
        ttk.Label(f,text='Requer Core autenticado, aberto com usuários ON-LINE visíveis.',wraplength=360).pack(pady=12)
    def start(self):
        u=norm(self.user.get())
        if not re.fullmatch(r'[A-Z0-9]+(?:_[A-Z0-9]+)?',u): return messagebox.showerror('ID inválido','Informe um ID como 422S ou 422S_4')
        if not messagebox.askyesno('Preparar leitura do Core',f'ID: {u}\n\nApós confirmar, você terá 7 segundos para clicar na janela do GO-Global e deixar visível a lista de Usuários ON-LINE.\n\nO programa só realizará a desconexão se encontrar uma única sessão correspondente.\n\nContinuar?'): return
        self.btn.config(state='disabled');self.root.withdraw()
        threading.Thread(target=self.work,args=(u,),daemon=True).start()
    def work(self,u):
        result=None
        try:
            time.sleep(7);a=find_session(scan(),u)
            time.sleep(.5);b=find_session(scan(),u)
            if a[0]!=b[0] or max(abs(a[1]-b[1]),abs(a[2]-b[2]))>12: raise RuntimeError('A lista mudou. Tente novamente.')
            pg.click(*center(b),button='right');time.sleep(.8)
            menu=find_menu(scan());pg.click(*center(menu))
            result=('info','Comando solicitado para '+b[0]+'. Verifique a lista do Core.')
        except Exception as e:
            pg.press('esc'); result=('error',str(e))
        def done():
            self.root.deiconify();self.btn.config(state='normal')
            (messagebox.showinfo if result[0]=='info' else messagebox.showerror)('Resultado',result[1])
        self.root.after(0,done)
if __name__=='__main__': App().root.mainloop()
