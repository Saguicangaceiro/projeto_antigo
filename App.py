import asyncio
import os
import json
import sys
import ctypes
from datetime import datetime
from typing import List, Dict, Any

# Bibliotecas de SNMP e PDF
import pysnmp.hlapi.v3arch.asyncio as hlapi
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# ================= CONFIGURAÇÃO DE TELA (WINDOWS) =================
def configurar_terminal(nome_exibicao="INKSIGHT"):
    """Ajusta o tamanho da fonte, título e dimensões da janela do CMD"""
    if os.name == 'nt':
        # 1. Título da Janela
        os.system(f"title {nome_exibicao} - Auditoria de Impressoras")
        
        # 2. Tamanho do Bloco (Colunas=120, Linhas=35)
        os.system('mode con: cols=90 lines=30')
        
        # 3. Configuração de Fonte Profissional
        STD_OUTPUT_HANDLE = -11
        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

        class CONSOLE_FONT_INFOEX(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_ulong),
                        ("nFont", ctypes.c_ulong),
                        ("dwFontSize", COORD),
                        ("FontFamily", ctypes.c_uint),
                        ("FontWeight", ctypes.c_uint),
                        ("FaceName", ctypes.c_wchar * 32)]

        handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        font = CONSOLE_FONT_INFOEX()
        font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX())
        font.dwFontSize.X = 0
        font.dwFontSize.Y = 20  # Tamanho da letra
        font.FontWeight = 400
        font.FaceName = "Consolas"
        ctypes.windll.kernel32.SetCurrentConsoleFontEx(handle, 0, ctypes.byref(font))

# ================= ESTILOS E CORES (ANSI) =================
class Theme:
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    HEADER_PDF = colors.HexColor('#2C3E50')
    ZEBRA_LIGHT = colors.HexColor('#F2F4F4')

# ================= GESTÃO DE ARQUIVOS E CONFIGS =================
class ConfigManager:
    def __init__(self, printers_path="impressoras.json", settings_path="config.json"):
        self.printers_path = printers_path
        self.settings_path = settings_path

    def load_printers(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.printers_path): return []
        try:
            with open(self.printers_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []

    def save_printer(self, ip: str, nome: str, setor: str):
        printers = self.load_printers()
        printers = [p for p in printers if p['ip'] != ip]
        printers.append({"ip": ip, "nome": nome, "setor": setor})
        with open(self.printers_path, 'w', encoding='utf-8') as f:
            json.dump(printers, f, indent=4, ensure_ascii=False)

    def remove_printer(self, ip: str) -> bool:
        printers = self.load_printers()
        new_list = [p for p in printers if p['ip'] != ip]
        if len(printers) != len(new_list):
            with open(self.printers_path, 'w', encoding='utf-8') as f:
                json.dump(new_list, f, indent=4, ensure_ascii=False)
            return True
        return False

    def get_sys_name(self) -> str:
        if not os.path.exists(self.settings_path): return "INKSIGHT"
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                return json.load(f).get("nome_sistema", "INKSIGHT")
        except: return "INKSIGHT"

    def set_sys_name(self, novo_nome: str):
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump({"nome_sistema": novo_nome}, f, indent=4, ensure_ascii=False)

# ================= MOTOR SNMP =================
class ScannerSNMP:
    OIDS = {
        "modelo": '1.3.6.1.2.1.1.1.0',
        "serial": '1.3.6.1.2.1.43.5.1.1.17.1',
        "contador": '1.3.6.1.2.1.43.10.2.1.4.1.1',
        "toner_atual": '1.3.6.1.2.1.43.11.1.1.9.1.1',
        "toner_max": '1.3.6.1.2.1.43.11.1.1.8.1.1'
    }

    @staticmethod
    def limpar_modelo(modelo_bruto: str) -> str:
        if not modelo_bruto: return "N/A"
        limpo = modelo_bruto.split(',')[0].split(';')[0].split(' - ')[0]
        for t in ["Ver.", "Firmware", "FW", "Built", "V1."]:
            if t in limpo: limpo = limpo.split(t)[0]
        return limpo.strip()[:25]

    @staticmethod
    async def fetch(printer_info: Dict[str, str]) -> Dict[str, Any]:
        ip = printer_info['ip']
        engine = hlapi.SnmpEngine()
        res = {**printer_info, "status": "OFFLINE", "contador": "0", "toner": "-", "modelo_real": "N/A", "serial": "-"}
        try:
            transport = await hlapi.UdpTransportTarget.create((ip, 161), timeout=1.2, retries=1)
            objs = [hlapi.ObjectType(hlapi.ObjectIdentity(oid)) for oid in ScannerSNMP.OIDS.values()]
            result = await hlapi.get_cmd(engine, hlapi.CommunityData('public', mpModel=0), transport, hlapi.ContextData(), *objs)
            err, _, _, varBinds = result
            if not err:
                res["status"] = "ONLINE"
                res["modelo_real"] = ScannerSNMP.limpar_modelo(varBinds[0][1].prettyPrint())
                res["serial"] = varBinds[1][1].prettyPrint().strip()
                res["contador"] = varBinds[2][1].prettyPrint() or "0"
                try:
                    cur, m_max = int(varBinds[3][1]), int(varBinds[4][1])
                    res["toner"] = f"{int((cur/m_max)*100)}%" if m_max > 0 else "OK"
                except: res["toner"] = "OK"
        except: pass
        finally: engine.close_dispatcher()
        return res

# ================= RELATÓRIO PDF =================
class ReportGenerator:
    @staticmethod
    def _header_footer(canvas, doc, nome_empresa):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setStrokeColor(Theme.HEADER_PDF)
        canvas.line(1*cm, 1.2*cm, landscape(A4)[0]-1*cm, 1.2*cm)
        page_num = canvas.getPageNumber()
        text = f"{nome_empresa} | Relatório de Impressoras | Página {page_num}"
        canvas.drawCentredString(landscape(A4)[0]/2, 0.8*cm, text)
        canvas.restoreState()

    @staticmethod
    def create_pdf(data: List[Dict[str, Any]], nome_empresa: str):
        filename = f"Relatorio_Auditoria_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=landscape(A4), margins=(1*cm, 1*cm, 1*cm, 1.5*cm))
        elements = []
        styles = getSampleStyleSheet()

        title = styles['Title']
        title.textColor = Theme.HEADER_PDF
        elements.append(Paragraph(f"<b>{nome_empresa.upper()}</b> - Relatório Impressoras", title))
        elements.append(Spacer(1, 15))

        headers = ["SETOR", "NOME/ID", "MODELO", "IP", "CONTADOR", "SERIAL", "STATUS"]
        table_data = [headers]

        for d in sorted(data, key=lambda x: x['setor']):
            status_html = f"<font color='green'><b>{d['status']}</b></font>" if d['status'] == "ONLINE" else f"<font color='red'><b>{d['status']}</b></font>"
            cnt_fmt = f"{int(d['contador']):,}".replace(',', '.')
            table_data.append([
                d['setor'].upper()[:12], d['nome'][:15], d['modelo_real'], d['ip'],
                cnt_fmt, d['serial'][:20], Paragraph(status_html, styles['Normal'])
            ])

        tbl = Table(table_data, colWidths=[3.0*cm, 3.5*cm, 4.5*cm, 3.2*cm, 2.8*cm, 4.5*cm, 1.8*cm, 2.5*cm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Theme.HEADER_PDF),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, Theme.ZEBRA_LIGHT]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(tbl)
        doc.build(elements, onFirstPage=lambda c, d: ReportGenerator._header_footer(c, d, nome_empresa), 
                  onLaterPages=lambda c, d: ReportGenerator._header_footer(c, d, nome_empresa))
        print(f"\n{Theme.GREEN}✅ Relatório salvo com sucesso!{Theme.RESET}")

# ================= APP PRINCIPAL =================
class App:
    def __init__(self):
        self.config = ConfigManager()

    def banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        nome = self.config.get_sys_name()
        print(f"{Theme.CYAN}{Theme.BOLD}")
        print(f"  {'='*60}")
        print(f"  {nome.center(58)}")
        print(f"  {'='*60}")
        print(f"  {Theme.YELLOW}:: GESTÃO E AUDITORIA DE IMPRESSORAS ::{Theme.RESET}\n")

    async def dashboard(self):
        printers = self.config.load_printers()
        if not printers: return
        self.banner()
        print(f"{Theme.YELLOW}🔄 Consultando dispositivos...{Theme.RESET}")
        results = await asyncio.gather(*[ScannerSNMP.fetch(p) for p in printers])
        self.banner()
        head = f"{'SETOR':<12} | {'NOME/ID':<15} | {'IP':<13} | {'PÁGINAS':<12} | {'STATUS':<9} | {'TONER'}"
        print(f"{Theme.BOLD}{head}{Theme.RESET}")
        print("-" * 100)
        for r in results:
            color = Theme.GREEN if r['status'] == "ONLINE" else Theme.RED
            cnt_fmt = f"{int(r['contador']):,}".replace(',', '.')
            print(f"{r['setor']:<12} | {r['nome']:<15} | {r['ip']:<13} | {cnt_fmt:<12} | {color}{r['status']:<9}{Theme.RESET} | {r['toner']}")
        input(f"\n[ENTER] Voltar...")

    def menu_config(self):
        while True:
            self.banner()
            print(f"{Theme.BOLD}CONFIGURAÇÕES:{Theme.RESET}")
            print(f"[1] Adicionar Impressora")
            print(f"[2] Remover Impressora")
            print(f"[3] Alterar Nome do Sistema/Empresa")
            print(f"[0] Voltar")
            op = input(f"\n{Theme.BOLD}Escolha: {Theme.RESET}")
            if op == '1':
                ip = input("IP: "); s = input("Setor: "); n = input("Nome/ID: ")
                if ip and s and n: self.config.save_printer(ip, n, s)
            elif op == '2':
                self.config.remove_printer(input("IP para remover: "))
            elif op == '3':
                novo = input("Novo nome: ")
                if novo: 
                    self.config.set_sys_name(novo)
                    configurar_terminal(novo) # Atualiza o título na hora
            elif op == '0': break

    async def run(self):
        while True:
            self.banner()
            print(f"{Theme.CYAN}[1]{Theme.RESET} 📄 Gerar Relatório PDF")
            print(f"{Theme.CYAN}[2]{Theme.RESET} 📟 Dashboard Real-time")
            print(f"{Theme.CYAN}[3]{Theme.RESET} ⚙️ Configurações")
            print(f"{Theme.RED}[0]{Theme.RESET} 🚪 Sair")
            choice = input(f"\n{Theme.BOLD}Escolha: {Theme.RESET}")
            if choice == '1':
                printers = self.config.load_printers()
                if printers:
                    res = await asyncio.gather(*[ScannerSNMP.fetch(p) for p in printers])
                    ReportGenerator.create_pdf(res, self.config.get_sys_name())
                    input("\n[ENTER]...")
            elif choice == '2': await self.dashboard()
            elif choice == '3': self.menu_config()
            elif choice == '0': break

if __name__ == "__main__":
    # 1. Carrega o nome primeiro para configurar a janela
    temp_config = ConfigManager()
    sys_name = temp_config.get_sys_name()
    
    # 2. Configura o terminal
    configurar_terminal(sys_name)
    
    # 3. Inicia o App
    app = App()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        sys.exit()