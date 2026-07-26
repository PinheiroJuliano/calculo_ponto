from copy import deepcopy
import ctypes
from datetime import datetime, timedelta
import json
import math
import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import colorchooser, font as tkfont, messagebox
import webbrowser
import winreg

import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray

from historico import (
    atualizar_registro,
    calcular_estatisticas,
    carregar_historico,
    formatar_duracao,
    salvar_historico,
)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


PALETAS = {
    "Azul": {
        "destaque": "#2563EB",
        "hover": "#1D4ED8",
        "marca": "#38BDF8",
    },
    "Verde": {
        "destaque": "#16A34A",
        "hover": "#15803D",
        "marca": "#4ADE80",
    },
    "Roxo": {
        "destaque": "#9333EA",
        "hover": "#7E22CE",
        "marca": "#C084FC",
    },
    "Âmbar": {
        "destaque": "#D97706",
        "hover": "#B45309",
        "marca": "#FBBF24",
    },
}

APARENCIAS = {
    "Escuro": {
        "modo": "dark",
        "fundo": "#0B1120",
        "painel": "#151E31",
        "entrada": "#0F172A",
        "texto": "#F8FAFC",
        "secundario": "#94A3B8",
    },
    "Claro": {
        "modo": "light",
        "fundo": "#EAF2F8",
        "painel": "#FFFFFF",
        "entrada": "#F8FAFC",
        "texto": "#172033",
        "secundario": "#64748B",
    },
    "Sistema": {
        "modo": "system",
        "fundo": ("#EAF2F8", "#0B1120"),
        "painel": ("#FFFFFF", "#151E31"),
        "entrada": ("#F8FAFC", "#0F172A"),
        "texto": ("#172033", "#F8FAFC"),
        "secundario": ("#64748B", "#94A3B8"),
    },
}

COR_TRANSPARENTE = "#010203"
CORES_MARCA_PADRAO = {
    "agora": "#94A3B8",
    "saida": "#38BDF8",
    "restante": "#38BDF8",
    "hora_extra": "#F43F5E",
}
CONFIG_PADRAO = {
    "aparencia": "Escuro",
    "paleta": "Azul",
    "exibir_marca": False,
    "atalho_marca": "Ctrl+Alt+M",
    "fonte_marca": "Segoe UI",
    "tamanho_fonte_marca": 15,
    "cores_marca": CORES_MARCA_PADRAO,
    "posicao_marca": None,
    "intervalo_historico": 30,
}
NOMES_CORES = {
    "agora": "Hora atual",
    "saida": "Saída prevista",
    "restante": "Tempo restante",
    "hora_extra": "Hora extra",
}
RE_COR_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
CHAVE_INICIALIZACAO_WINDOWS = (
    r"Software\Microsoft\Windows\CurrentVersion\Run"
)
NOME_INICIALIZACAO_WINDOWS = "CalculoPonto"
VERSAO_PADRAO = "0.0.0"
INTERVALOS_HISTORICO = (5, 10, 30, 60, 120)
MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)
CONTRIBUIDORES = (
    {
        "nome": "Carlos Orlandi",
        "usuario": "tosuki",
        "url": "https://github.com/tosuki",
    },
    {
        "nome": "lucashfsdev",
        "usuario": "lucasfhs",
        "url": "https://github.com/lucasfhs",
    },
    {
        "nome": "PisJuliano",
        "usuario": "PisJuliano",
        "url": "https://github.com/PisJuliano",
    },
)

MODIFICADORES_ATALHO = {
    "CTRL": ("Ctrl", 0x0002),
    "CONTROL": ("Ctrl", 0x0002),
    "ALT": ("Alt", 0x0001),
    "SHIFT": ("Shift", 0x0004),
    "WIN": ("Win", 0x0008),
    "WINDOWS": ("Win", 0x0008),
}
ORDEM_MODIFICADORES = ("Ctrl", "Alt", "Shift", "Win")
TECLAS_ESPECIAIS = {
    "SPACE": ("Espaço", 0x20),
    "ESPAÇO": ("Espaço", 0x20),
    "ESPACO": ("Espaço", 0x20),
    "HOME": ("Home", 0x24),
    "END": ("End", 0x23),
    "INSERT": ("Insert", 0x2D),
    "DELETE": ("Delete", 0x2E),
    "PAGEUP": ("PageUp", 0x21),
    "PAGEDOWN": ("PageDown", 0x22),
}


def decodificar_atalho(atalho):
    """Normaliza um atalho e retorna seu texto, modificadores e virtual key."""
    if not isinstance(atalho, str):
        raise ValueError("Informe um atalho de teclado.")

    partes = [parte.strip() for parte in atalho.split("+")]
    if not partes or any(not parte for parte in partes):
        raise ValueError("Use o formato Ctrl+Alt+M.")

    modificadores = {}
    tecla = None
    virtual_key = None
    for parte in partes:
        nome = parte.upper()
        if nome in MODIFICADORES_ATALHO:
            rotulo, valor = MODIFICADORES_ATALHO[nome]
            modificadores[rotulo] = valor
            continue
        if tecla is not None:
            raise ValueError("O atalho deve conter apenas uma tecla principal.")
        if len(nome) == 1 and ("A" <= nome <= "Z" or "0" <= nome <= "9"):
            tecla, virtual_key = nome, ord(nome)
        elif re.fullmatch(r"F(?:[1-9]|1[0-9]|2[0-4])", nome):
            numero = int(nome[1:])
            tecla, virtual_key = nome, 0x70 + numero - 1
        elif nome in TECLAS_ESPECIAIS:
            tecla, virtual_key = TECLAS_ESPECIAIS[nome]
        else:
            raise ValueError(f"A tecla “{parte}” não é suportada.")

    if tecla is None:
        raise ValueError("Inclua uma tecla principal no atalho.")
    if not modificadores and not tecla.startswith("F"):
        raise ValueError("Use Ctrl, Alt, Shift ou Win junto com a tecla.")

    nomes = [
        nome for nome in ORDEM_MODIFICADORES if nome in modificadores
    ]
    texto = "+".join([*nomes, tecla])
    mascara = sum(modificadores.values())
    return texto, mascara, virtual_key


class AtalhoGlobalWindows:
    """Registra um atalho global sem instalar um gancho de teclado."""

    WM_HOTKEY = 0x0312
    WM_QUIT = 0x0012
    MOD_NOREPEAT = 0x4000
    IDENTIFICADOR = 1

    class Ponto(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    class Mensagem(ctypes.Structure):
        pass

    Mensagem._fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_ssize_t),
        ("time", ctypes.c_ulong),
        ("pt", Ponto),
        ("lPrivate", ctypes.c_ulong),
    ]

    def __init__(self, callback):
        self.callback = callback
        self.thread = None
        self.thread_id = None
        self._pronto = None
        self._erro = None

    def configurar(self, atalho):
        _texto, modificadores, virtual_key = decodificar_atalho(atalho)
        self.parar()
        self._pronto = threading.Event()
        self._erro = None
        self.thread = threading.Thread(
            target=self._executar,
            args=(modificadores, virtual_key),
            name="atalho-global-marca",
            daemon=True,
        )
        self.thread.start()
        if not self._pronto.wait(timeout=2):
            self.parar()
            raise OSError("O Windows não respondeu ao registro do atalho.")
        if self._erro is not None:
            erro = self._erro
            self.parar()
            raise erro

    def _executar(self, modificadores, virtual_key):
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.thread_id = kernel32.GetCurrentThreadId()
        registrado = user32.RegisterHotKey(
            None,
            self.IDENTIFICADOR,
            modificadores | self.MOD_NOREPEAT,
            virtual_key,
        )
        if not registrado:
            codigo = ctypes.get_last_error()
            self._erro = OSError(
                codigo,
                "O atalho já está em uso por outro programa."
                if codigo == 1409
                else "Não foi possível registrar o atalho global.",
            )
            self._pronto.set()
            return

        self._pronto.set()
        mensagem = self.Mensagem()
        try:
            while user32.GetMessageW(
                ctypes.byref(mensagem), None, 0, 0
            ) > 0:
                if (
                    mensagem.message == self.WM_HOTKEY
                    and mensagem.wParam == self.IDENTIFICADOR
                ):
                    self.callback()
        finally:
            user32.UnregisterHotKey(None, self.IDENTIFICADOR)

    def parar(self):
        thread = self.thread
        if thread is None:
            return
        if thread.is_alive() and self.thread_id is not None:
            ctypes.windll.user32.PostThreadMessageW(
                self.thread_id, self.WM_QUIT, 0, 0
            )
            thread.join(timeout=2)
        self.thread = None
        self.thread_id = None


class InformacaoVersao(ctypes.Structure):
    _fields_ = [
        ("assinatura", ctypes.c_uint32),
        ("versao_estrutura", ctypes.c_uint32),
        ("versao_arquivo_ms", ctypes.c_uint32),
        ("versao_arquivo_ls", ctypes.c_uint32),
        ("versao_produto_ms", ctypes.c_uint32),
        ("versao_produto_ls", ctypes.c_uint32),
        ("mascara_flags", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("sistema_operacional", ctypes.c_uint32),
        ("tipo_arquivo", ctypes.c_uint32),
        ("subtipo_arquivo", ctypes.c_uint32),
        ("data_arquivo_ms", ctypes.c_uint32),
        ("data_arquivo_ls", ctypes.c_uint32),
    ]


def obter_versao_aplicativo():
    """Lê a versão do executável gerado e usa 0.0.0 no modo de desenvolvimento."""
    versao_ambiente = os.getenv("CALCULO_PONTO_VERSION", "").strip()
    if versao_ambiente:
        return versao_ambiente
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return VERSAO_PADRAO

    try:
        version = ctypes.windll.version
        tamanho = version.GetFileVersionInfoSizeW(sys.executable, None)
        if not tamanho:
            return VERSAO_PADRAO
        dados = ctypes.create_string_buffer(tamanho)
        if not version.GetFileVersionInfoW(
            sys.executable, 0, tamanho, dados
        ):
            return VERSAO_PADRAO
        ponteiro = ctypes.c_void_p()
        comprimento = ctypes.c_uint()
        if not version.VerQueryValueW(
            dados,
            "\\",
            ctypes.byref(ponteiro),
            ctypes.byref(comprimento),
        ):
            return VERSAO_PADRAO
        info = ctypes.cast(
            ponteiro, ctypes.POINTER(InformacaoVersao)
        ).contents
        partes = (
            info.versao_arquivo_ms >> 16,
            info.versao_arquivo_ms & 0xFFFF,
            info.versao_arquivo_ls >> 16,
            info.versao_arquivo_ls & 0xFFFF,
        )
        while len(partes) > 3 and partes[-1] == 0:
            partes = partes[:-1]
        return ".".join(str(parte) for parte in partes)
    except (AttributeError, OSError, ValueError):
        return VERSAO_PADRAO


def caminho_configuracao():
    base = os.getenv("APPDATA")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "CalculoPonto", "config.json")


def caminho_historico():
    return os.path.join(
        os.path.dirname(caminho_configuracao()), "historico.json"
    )


def caminho_recurso(caminho_relativo):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, caminho_relativo)


def comando_inicializacao_windows():
    if getattr(sys, "frozen", False):
        argumentos = [os.path.abspath(sys.executable), "--bandeja"]
    else:
        executavel_python = os.path.abspath(sys.executable)
        pasta_python = os.path.dirname(executavel_python)
        nome_pythonw = "pythonw.exe"
        if os.name != "nt":
            nome_pythonw = os.path.basename(executavel_python)
        pythonw = os.path.join(pasta_python, nome_pythonw)
        if not os.path.exists(pythonw):
            pythonw = executavel_python
        argumentos = [
            pythonw,
            os.path.abspath(__file__),
            "--bandeja",
        ]
    return subprocess.list2cmdline(argumentos)


def ler_inicializacao_windows():
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            CHAVE_INICIALIZACAO_WINDOWS,
            0,
            winreg.KEY_READ,
        ) as chave:
            comando, _tipo = winreg.QueryValueEx(
                chave, NOME_INICIALIZACAO_WINDOWS
            )
            return comando if isinstance(comando, str) else None
    except OSError:
        return None


def configurar_inicializacao_windows(ativar):
    if ativar:
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            CHAVE_INICIALIZACAO_WINDOWS,
            0,
            winreg.KEY_SET_VALUE,
        ) as chave:
            winreg.SetValueEx(
                chave,
                NOME_INICIALIZACAO_WINDOWS,
                0,
                winreg.REG_SZ,
                comando_inicializacao_windows(),
            )
        return

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            CHAVE_INICIALIZACAO_WINDOWS,
            0,
            winreg.KEY_SET_VALUE,
        ) as chave:
            winreg.DeleteValue(chave, NOME_INICIALIZACAO_WINDOWS)
    except FileNotFoundError:
        pass


def carregar_configuracao():
    config = deepcopy(CONFIG_PADRAO)
    try:
        with open(caminho_configuracao(), "r", encoding="utf-8") as arquivo:
            salva = json.load(arquivo)
    except (OSError, ValueError, TypeError):
        return config

    if salva.get("aparencia") in APARENCIAS:
        config["aparencia"] = salva["aparencia"]
    if salva.get("paleta") in PALETAS:
        config["paleta"] = salva["paleta"]
    if isinstance(salva.get("exibir_marca"), bool):
        config["exibir_marca"] = salva["exibir_marca"]
    try:
        config["atalho_marca"] = decodificar_atalho(
            salva.get("atalho_marca")
        )[0]
    except ValueError:
        pass
    if isinstance(salva.get("fonte_marca"), str) and salva["fonte_marca"].strip():
        config["fonte_marca"] = salva["fonte_marca"].strip()

    tamanho = salva.get("tamanho_fonte_marca")
    if isinstance(tamanho, (int, float)) and 9 <= tamanho <= 36:
        config["tamanho_fonte_marca"] = int(tamanho)

    cores = salva.get("cores_marca")
    if isinstance(cores, dict):
        for chave in CORES_MARCA_PADRAO:
            if isinstance(cores.get(chave), str) and RE_COR_HEX.fullmatch(
                cores[chave]
            ):
                config["cores_marca"][chave] = cores[chave].upper()

    posicao = salva.get("posicao_marca")
    if (
        isinstance(posicao, list)
        and len(posicao) == 2
        and all(isinstance(valor, int) for valor in posicao)
    ):
        config["posicao_marca"] = posicao

    intervalo = salva.get("intervalo_historico")
    if intervalo in INTERVALOS_HISTORICO:
        config["intervalo_historico"] = intervalo

    return config


class CalculadoraSaida(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.configuracao = carregar_configuracao()
        self.aparencia_atual = self.configuracao["aparencia"]
        self.paleta_atual = self.configuracao["paleta"]
        self.iniciado_na_bandeja = "--bandeja" in sys.argv[1:]
        ctk.set_appearance_mode(APARENCIAS[self.aparencia_atual]["modo"])

        self.title("Calculadora de Saída")
        self.geometry("460x840")
        self.minsize(460, 775)
        self.resizable(False, True)
        self.protocol("WM_DELETE_WINDOW", self.ocultar_na_bandeja)

        self.marca_dagua = None
        self.labels_marca = {}
        self.janela_personalizacao = None
        self.janela_menu_paginas = None
        self.janela_historico = None
        self.janela_estatisticas = None
        self.janela_sobre = None
        self.botoes_cores = {}
        self.cards_estatisticas = {}
        self.arraste_marca = None
        self.icone_bandeja = None
        self.comandos_bandeja = queue.Queue()
        self.atalho_global = None
        self.historico_after_id = None
        self.historico = carregar_historico(caminho_historico())
        self.versao = obter_versao_aplicativo()
        self.encerrando = False

        self.aparencia_var = tk.StringVar(value=self.aparencia_atual)
        self.paleta_var = tk.StringVar(value=self.paleta_atual)
        self.marca_var = tk.BooleanVar(value=self.configuracao["exibir_marca"])
        self.atalho_marca_var = tk.StringVar(
            value=self.configuracao["atalho_marca"]
        )
        comando_inicio = ler_inicializacao_windows()
        self.iniciar_windows_var = tk.BooleanVar(
            value=comando_inicio is not None
        )
        if (
            comando_inicio is not None
            and comando_inicio != comando_inicializacao_windows()
        ):
            try:
                configurar_inicializacao_windows(True)
            except OSError:
                pass
        self.fonte_marca_var = tk.StringVar(
            value=self.configuracao["fonte_marca"]
        )
        self.tipo_grafico_var = tk.StringVar(value="Linhas")
        self.intervalo_historico_var = tk.StringVar(
            value=f"{self.configuracao['intervalo_historico']} segundos"
        )
        self.criar_menu_paginas()

        self.titulo = ctk.CTkLabel(
            self,
            text="Calculadora de Saída",
            font=("Segoe UI", 26, "bold"),
        )
        self.titulo.pack(pady=(18, 10))

        self.formulario = ctk.CTkFrame(self, corner_radius=16)
        self.formulario.pack(fill="x", padx=24)

        self.rotulos_campos = []
        self.entradas = []
        self.entrada = self.criar_campo(
            self.formulario, "Hora de entrada (HH:MM)", "08:00"
        )
        self.almoco = self.criar_campo(
            self.formulario, "Almoço (minutos)", "60"
        )
        self.jornada = self.criar_campo(
            self.formulario, "Jornada (horas)", "8"
        )

        self.preferencias = ctk.CTkFrame(self, corner_radius=16)
        self.preferencias.pack(fill="x", padx=24, pady=(12, 0))
        self.preferencias.grid_columnconfigure(1, weight=1)

        self.lbl_aparencia = ctk.CTkLabel(
            self.preferencias,
            text="Aparência",
            font=("Segoe UI", 14, "bold"),
        )
        self.lbl_aparencia.grid(
            row=0, column=0, padx=(16, 8), pady=(13, 6), sticky="w"
        )

        self.seletor_aparencia = ctk.CTkOptionMenu(
            self.preferencias,
            values=list(APARENCIAS),
            variable=self.aparencia_var,
            command=self.aplicar_aparencia,
            width=126,
        )
        self.seletor_aparencia.grid(
            row=0, column=1, padx=(8, 16), pady=(13, 6), sticky="e"
        )

        self.lbl_paleta = ctk.CTkLabel(
            self.preferencias,
            text="Cor de destaque",
            font=("Segoe UI", 13),
        )
        self.lbl_paleta.grid(
            row=1, column=0, padx=(16, 8), pady=6, sticky="w"
        )

        self.seletor_paleta = ctk.CTkOptionMenu(
            self.preferencias,
            values=list(PALETAS),
            variable=self.paleta_var,
            command=self.aplicar_paleta,
            width=126,
        )
        self.seletor_paleta.grid(
            row=1, column=1, padx=(8, 16), pady=6, sticky="e"
        )

        self.check_marca = ctk.CTkCheckBox(
            self.preferencias,
            text="Exibir marca d'água sobre as janelas",
            variable=self.marca_var,
            command=self.alternar_marca_dagua,
            font=("Segoe UI", 13),
        )
        self.check_marca.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(8, 7), sticky="w"
        )

        self.check_iniciar_windows = ctk.CTkCheckBox(
            self.preferencias,
            text="Iniciar com o Windows",
            variable=self.iniciar_windows_var,
            command=self.alternar_inicializacao_windows,
            font=("Segoe UI", 13),
        )
        self.check_iniciar_windows.grid(
            row=5,
            column=0,
            columnspan=2,
            padx=16,
            pady=(7, 7),
            sticky="w",
        )

        self.lbl_atalho_marca = ctk.CTkLabel(
            self.preferencias,
            text="Atalho (ocultar/desocultar) da marca d'água",
            font=("Segoe UI", 13),
        )
        self.lbl_atalho_marca.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=16,
            pady=(7, 2),
            sticky="w",
        )

        self.entrada_atalho_marca = ctk.CTkEntry(
            self.preferencias,
            textvariable=self.atalho_marca_var,
            width=126,
            justify="center",
        )
        self.entrada_atalho_marca.grid(
            row=4,
            column=0,
            columnspan=2,
            padx=16,
            pady=(2, 7),
            sticky="ew",
        )
        self.entrada_atalho_marca.bind(
            "<Return>", self.aplicar_atalho_marca
        )
        self.entrada_atalho_marca.bind(
            "<FocusOut>", self.aplicar_atalho_marca
        )

        self.botao_personalizar = ctk.CTkButton(
            self.preferencias,
            text="Personalizar marca d'água",
            command=self.abrir_personalizacao_marca,
            height=32,
        )
        self.botao_personalizar.grid(
            row=6,
            column=0,
            columnspan=2,
            padx=16,
            pady=(4, 7),
            sticky="ew",
        )

        self.botao_bandeja = ctk.CTkButton(
            self.preferencias,
            text="Ocultar na bandeja do Windows",
            command=self.ocultar_na_bandeja,
            height=32,
        )
        self.botao_bandeja.grid(
            row=7,
            column=0,
            columnspan=2,
            padx=16,
            pady=(7, 14),
            sticky="ew",
        )

        self.lbl_agora = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 14)
        )
        self.lbl_agora.pack(pady=(18, 4))

        self.lbl_saida = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 19, "bold")
        )
        self.lbl_saida.pack()

        self.lbl_restante = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 19)
        )
        self.lbl_restante.pack(pady=(7, 12))

        self.aplicar_tema_visual()
        self.iniciar_bandeja()
        self.iniciar_atalho_global()
        self.after(100, self.processar_comandos_bandeja)
        self.agendar_registro_historico()
        if self.iniciado_na_bandeja and self.icone_bandeja is not None:
            self.withdraw()
        if self.marca_var.get():
            self.after(150, self.criar_marca_dagua)
        self.atualizar()

    def criar_campo(self, frame, texto, valor):
        rotulo = ctk.CTkLabel(frame, text=texto, font=("Segoe UI", 13))
        rotulo.pack(pady=(11 if not self.rotulos_campos else 7, 4))
        self.rotulos_campos.append(rotulo)

        campo = ctk.CTkEntry(frame, height=34)
        campo.insert(0, valor)
        campo.pack(padx=18, fill="x")
        self.entradas.append(campo)
        return campo

    def criar_menu_paginas(self):
        self.botao_paginas = ctk.CTkButton(
            self,
            text="Menu",
            width=72,
            height=28,
            corner_radius=9,
            font=("Segoe UI", 11, "bold"),
            command=self.alternar_menu_paginas,
        )
        self.botao_paginas.place(
            relx=1, x=-18, y=18, anchor="ne"
        )
        self.bind("<Control-h>", lambda _evento: self.abrir_historico())
        self.bind("<Control-e>", lambda _evento: self.abrir_estatisticas())
        self.bind("<Control-b>", lambda _evento: self.abrir_sobre())

    def alternar_menu_paginas(self):
        if (
            self.janela_menu_paginas is not None
            and self.janela_menu_paginas.winfo_exists()
        ):
            self.fechar_menu_paginas()
            return

        janela = ctk.CTkToplevel(self)
        janela.overrideredirect(True)
        janela.attributes("-topmost", True)
        janela.transient(self)
        janela.configure(border_width=1)
        janela.geometry("210x166")
        janela.grid_columnconfigure(0, weight=1)
        self.janela_menu_paginas = janela

        self.lbl_menu_paginas = ctk.CTkLabel(
            janela,
            text="Abrir página",
            font=("Segoe UI", 12, "bold"),
        )
        self.lbl_menu_paginas.grid(
            row=0, column=0, padx=12, pady=(10, 5), sticky="w"
        )

        self.botoes_menu_paginas = []
        opcoes = (
            ("Histórico", "Ctrl+H", self.abrir_historico),
            ("Estatísticas", "Ctrl+E", self.abrir_estatisticas),
            ("Sobre", "Ctrl+B", self.abrir_sobre),
        )
        for linha, (rotulo, atalho, comando) in enumerate(opcoes, start=1):
            botao = ctk.CTkButton(
                janela,
                text=f"{rotulo}     {atalho}",
                height=34,
                anchor="w",
                command=lambda acao=comando: self.abrir_pagina_menu(acao),
            )
            botao.grid(
                row=linha,
                column=0,
                padx=10,
                pady=(0, 6),
                sticky="ew",
            )
            self.botoes_menu_paginas.append(botao)

        self.aplicar_tema_menu_paginas()
        self.update_idletasks()
        janela.update_idletasks()
        x = (
            self.botao_paginas.winfo_rootx()
            + self.botao_paginas.winfo_width()
            - 210
        )
        y = (
            self.botao_paginas.winfo_rooty()
            + self.botao_paginas.winfo_height()
            + 7
        )
        tela_x, tela_y, largura_tela, altura_tela = self.limites_tela()
        x = min(
            max(tela_x + 8, x),
            tela_x + max(8, largura_tela - 218),
        )
        y = min(
            max(tela_y + 8, y),
            tela_y + max(8, altura_tela - 174),
        )
        janela.geometry(f"210x166+{x}+{y}")
        janela.bind("<Escape>", lambda _evento: self.fechar_menu_paginas())
        janela.bind(
            "<FocusOut>",
            lambda _evento: janela.after(120, self.fechar_menu_se_sem_foco),
        )
        janela.after(50, janela.focus_force)

    def abrir_pagina_menu(self, comando):
        self.fechar_menu_paginas()
        comando()

    def fechar_menu_se_sem_foco(self):
        if (
            self.janela_menu_paginas is None
            or not self.janela_menu_paginas.winfo_exists()
        ):
            return
        try:
            foco = self.focus_get()
            pertence_ao_menu = (
                foco is not None
                and foco.winfo_toplevel() is self.janela_menu_paginas
            )
        except tk.TclError:
            pertence_ao_menu = False
        if not pertence_ao_menu:
            self.fechar_menu_paginas()

    def fechar_menu_paginas(self):
        if (
            self.janela_menu_paginas is not None
            and self.janela_menu_paginas.winfo_exists()
        ):
            self.janela_menu_paginas.destroy()
        self.janela_menu_paginas = None
        self.botoes_menu_paginas = []

    def aplicar_tema_menu_paginas(self):
        visual = APARENCIAS[self.aparencia_atual]
        paleta = PALETAS[self.paleta_atual]
        self.botao_paginas.configure(
            fg_color=visual["painel"],
            hover_color=visual["entrada"],
            border_width=1,
            border_color=paleta["destaque"],
            text_color=visual["texto"],
        )
        if (
            self.janela_menu_paginas is None
            or not self.janela_menu_paginas.winfo_exists()
        ):
            return
        self.janela_menu_paginas.configure(
            fg_color=visual["painel"],
            border_color=paleta["destaque"],
        )
        self.lbl_menu_paginas.configure(text_color=visual["secundario"])
        for botao in self.botoes_menu_paginas:
            botao.configure(
                fg_color=visual["entrada"],
                hover_color=paleta["hover"],
                text_color=visual["texto"],
            )

    @staticmethod
    def resolver_cor(cor):
        if isinstance(cor, tuple):
            indice = (
                0
                if ctk.get_appearance_mode().lower() == "light"
                else 1
            )
            return cor[indice]
        return cor

    def agendar_registro_historico(self):
        if self.encerrando:
            return
        if self.historico_after_id is not None:
            try:
                self.after_cancel(self.historico_after_id)
            except (tk.TclError, ValueError):
                pass
        intervalo = self.configuracao["intervalo_historico"] * 1000
        self.historico_after_id = self.after(
            intervalo, self.registrar_historico_periodico
        )

    def registrar_historico_periodico(self):
        self.historico_after_id = None
        if self.encerrando:
            return
        self.registrar_historico()
        self.agendar_registro_historico()

    def registrar_historico(self, gravar=True):
        try:
            dados = self.calcular()
        except (TypeError, ValueError):
            return False

        momento = dados["momento"]
        registro = {
            "data": momento.date().isoformat(),
            "entrada": dados["entrada_dt"].strftime("%H:%M"),
            "almoco_minutos": dados["almoco_minutos"],
            "jornada_horas": dados["jornada_horas"],
            "saida_prevista": dados["saida_dt"].strftime("%H:%M"),
            "saldo_segundos": dados["saldo_segundos"],
            "atualizado_em": momento.isoformat(timespec="seconds"),
        }
        self.historico = atualizar_registro(self.historico, registro)
        if gravar:
            try:
                salvar_historico(
                    caminho_historico(), self.historico, momento
                )
            except OSError:
                return False
        self.atualizar_paginas_dados()
        return True

    def alterar_intervalo_historico(self, valor):
        try:
            intervalo = int(str(valor).split()[0])
        except (TypeError, ValueError):
            intervalo = self.configuracao["intervalo_historico"]
        if intervalo not in INTERVALOS_HISTORICO:
            intervalo = self.configuracao["intervalo_historico"]
        self.configuracao["intervalo_historico"] = intervalo
        self.intervalo_historico_var.set(f"{intervalo} segundos")
        self.salvar_configuracao()
        self.agendar_registro_historico()
        self.atualizar_paginas_dados()

    def abrir_historico(self):
        if (
            self.janela_historico is not None
            and self.janela_historico.winfo_exists()
        ):
            self.janela_historico.lift()
            self.janela_historico.focus_force()
            return

        self.registrar_historico(gravar=False)
        janela = ctk.CTkToplevel(self)
        janela.title("Histórico - Calculadora de Saída")
        janela.geometry("900x700")
        janela.minsize(760, 600)
        janela.transient(self)
        janela.protocol("WM_DELETE_WINDOW", self.fechar_historico)
        janela.grid_columnconfigure(0, weight=1)
        janela.grid_rowconfigure(3, weight=1)
        self.janela_historico = janela

        self.lbl_historico_titulo = ctk.CTkLabel(
            janela, text="Histórico", font=("Segoe UI", 24, "bold")
        )
        self.lbl_historico_titulo.grid(
            row=0, column=0, padx=24, pady=(20, 2)
        )
        self.lbl_historico_subtitulo = ctk.CTkLabel(
            janela,
            text="Saldo diário dos últimos 30 registros",
            font=("Segoe UI", 13),
        )
        self.lbl_historico_subtitulo.grid(
            row=1, column=0, padx=24, pady=(0, 12)
        )

        self.frame_controles_historico = ctk.CTkFrame(
            janela, corner_radius=14
        )
        self.frame_controles_historico.grid(
            row=2, column=0, padx=24, pady=(0, 12), sticky="ew"
        )
        self.frame_controles_historico.grid_columnconfigure(1, weight=1)
        self.frame_controles_historico.grid_columnconfigure(3, weight=1)

        self.lbl_tipo_grafico = ctk.CTkLabel(
            self.frame_controles_historico,
            text="Visualização",
            font=("Segoe UI", 13, "bold"),
        )
        self.lbl_tipo_grafico.grid(
            row=0, column=0, padx=(16, 8), pady=14, sticky="w"
        )
        self.seletor_tipo_grafico = ctk.CTkOptionMenu(
            self.frame_controles_historico,
            values=["Linhas", "Colunas"],
            variable=self.tipo_grafico_var,
            command=lambda _valor: self.desenhar_grafico_historico(),
            width=130,
        )
        self.seletor_tipo_grafico.grid(
            row=0, column=1, padx=(0, 20), pady=14, sticky="w"
        )

        self.lbl_intervalo_historico = ctk.CTkLabel(
            self.frame_controles_historico,
            text="Gravar a cada",
            font=("Segoe UI", 13, "bold"),
        )
        self.lbl_intervalo_historico.grid(
            row=0, column=2, padx=(16, 8), pady=14, sticky="e"
        )
        self.seletor_intervalo_historico = ctk.CTkOptionMenu(
            self.frame_controles_historico,
            values=[
                f"{intervalo} segundos"
                for intervalo in INTERVALOS_HISTORICO
            ],
            variable=self.intervalo_historico_var,
            command=self.alterar_intervalo_historico,
            width=145,
        )
        self.seletor_intervalo_historico.grid(
            row=0, column=3, padx=(0, 16), pady=14, sticky="e"
        )

        self.frame_grafico_historico = ctk.CTkFrame(
            janela, corner_radius=14
        )
        self.frame_grafico_historico.grid(
            row=3, column=0, padx=24, pady=(0, 12), sticky="nsew"
        )
        self.canvas_historico = tk.Canvas(
            self.frame_grafico_historico,
            highlightthickness=0,
            height=350,
        )
        self.canvas_historico.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas_historico.bind(
            "<Configure>",
            lambda _evento: self.canvas_historico.after_idle(
                self.desenhar_grafico_historico
            ),
        )

        self.frame_lista_historico = ctk.CTkFrame(
            janela, corner_radius=14
        )
        self.frame_lista_historico.grid(
            row=4, column=0, padx=24, pady=(0, 12), sticky="ew"
        )
        self.lbl_resumo_historico = ctk.CTkLabel(
            self.frame_lista_historico,
            text="",
            font=("Segoe UI", 13, "bold"),
        )
        self.lbl_resumo_historico.pack(
            anchor="w", padx=16, pady=(12, 4)
        )
        self.texto_registros_historico = ctk.CTkTextbox(
            self.frame_lista_historico,
            height=105,
            font=("Consolas", 12),
        )
        self.texto_registros_historico.pack(
            fill="x", padx=16, pady=(0, 14)
        )

        self.aplicar_tema_janela_historico()
        self.atualizar_pagina_historico()
        janela.after(100, janela.focus_force)

    def fechar_historico(self):
        if (
            self.janela_historico is not None
            and self.janela_historico.winfo_exists()
        ):
            self.janela_historico.destroy()
        self.janela_historico = None

    def atualizar_pagina_historico(self):
        if (
            self.janela_historico is None
            or not self.janela_historico.winfo_exists()
        ):
            return
        resumo = calcular_estatisticas(self.historico, datetime.now())
        self.lbl_resumo_historico.configure(
            text=(
                f"{resumo['dias']} dias registrados neste mês  •  "
                f"Saldo {formatar_duracao(resumo['saldo_segundos'], True)}"
            )
        )

        linhas = ["Data       Entrada  Saída   Saldo"]
        for item in reversed(self.historico[-6:]):
            data = datetime.fromisoformat(item["data"]).strftime("%d/%m/%Y")
            saldo = formatar_duracao(item["saldo_segundos"], True)
            linhas.append(
                f"{data}  {item['entrada']:>7}  "
                f"{item['saida_prevista']:>5}   {saldo}"
            )
        self.texto_registros_historico.configure(state="normal")
        self.texto_registros_historico.delete("1.0", "end")
        self.texto_registros_historico.insert("1.0", "\n".join(linhas))
        self.texto_registros_historico.configure(state="disabled")
        self.desenhar_grafico_historico()

    def desenhar_grafico_historico(self):
        if (
            self.janela_historico is None
            or not self.janela_historico.winfo_exists()
        ):
            return
        canvas = self.canvas_historico
        canvas.delete("all")
        largura = max(canvas.winfo_width(), 500)
        altura = max(canvas.winfo_height(), 280)
        visual = APARENCIAS[self.aparencia_atual]
        paleta = PALETAS[self.paleta_atual]
        fundo = self.resolver_cor(visual["painel"])
        texto = self.resolver_cor(visual["texto"])
        secundario = self.resolver_cor(visual["secundario"])
        grade = self.resolver_cor(visual["entrada"])
        canvas.configure(bg=fundo)

        registros = self.historico[-30:]
        if not registros:
            canvas.create_text(
                largura / 2,
                altura / 2,
                text="O gráfico aparecerá após o primeiro registro.",
                fill=secundario,
                font=("Segoe UI", 13),
            )
            return

        margem_esquerda, margem_direita = 70, 24
        margem_superior, margem_inferior = 30, 50
        esquerda = margem_esquerda
        direita = largura - margem_direita
        topo = margem_superior
        base = altura - margem_inferior
        valores = [item["saldo_segundos"] / 3600 for item in registros]
        minimo = min(0, min(valores))
        maximo = max(0, max(valores))
        amplitude = max(maximo - minimo, 1)
        minimo -= amplitude * 0.12
        maximo += amplitude * 0.12

        def coordenada_y(valor):
            proporcao = (valor - minimo) / (maximo - minimo)
            return base - proporcao * (base - topo)

        for indice in range(5):
            valor = minimo + (maximo - minimo) * indice / 4
            y = coordenada_y(valor)
            canvas.create_line(esquerda, y, direita, y, fill=grade)
            rotulo = f"{valor:+.1f}h".replace(".", ",")
            canvas.create_text(
                esquerda - 10,
                y,
                text=rotulo,
                anchor="e",
                fill=secundario,
                font=("Segoe UI", 10),
            )

        zero_y = coordenada_y(0)
        canvas.create_line(
            esquerda, zero_y, direita, zero_y, fill=secundario, width=2
        )
        passo = (direita - esquerda) / max(len(registros), 1)
        pontos = []
        for indice, (item, valor) in enumerate(zip(registros, valores)):
            x = esquerda + passo * (indice + 0.5)
            y = coordenada_y(valor)
            pontos.append((x, y, valor))

        if self.tipo_grafico_var.get() == "Colunas":
            largura_barra = max(6, min(34, passo * 0.58))
            for x, y, valor in pontos:
                cor = (
                    paleta["destaque"]
                    if valor >= 0
                    else CORES_MARCA_PADRAO["hora_extra"]
                )
                canvas.create_rectangle(
                    x - largura_barra / 2,
                    min(y, zero_y),
                    x + largura_barra / 2,
                    max(y, zero_y),
                    fill=cor,
                    outline="",
                )
        else:
            if len(pontos) > 1:
                coordenadas = [
                    coordenada
                    for x, y, _valor in pontos
                    for coordenada in (x, y)
                ]
                canvas.create_line(
                    *coordenadas,
                    fill=paleta["destaque"],
                    width=3,
                    smooth=True,
                )
            for x, y, valor in pontos:
                cor = (
                    paleta["marca"]
                    if valor >= 0
                    else CORES_MARCA_PADRAO["hora_extra"]
                )
                canvas.create_oval(
                    x - 5, y - 5, x + 5, y + 5, fill=cor, outline=fundo
                )

        espacamento_rotulos = max(1, math.ceil(len(registros) / 7))
        for indice, item in enumerate(registros):
            if (
                indice % espacamento_rotulos != 0
                and indice != len(registros) - 1
            ):
                continue
            x = esquerda + passo * (indice + 0.5)
            data = datetime.fromisoformat(item["data"]).strftime("%d/%m")
            canvas.create_text(
                x,
                base + 22,
                text=data,
                fill=texto,
                font=("Segoe UI", 10),
            )

    def aplicar_tema_janela_historico(self):
        if (
            self.janela_historico is None
            or not self.janela_historico.winfo_exists()
        ):
            return
        visual = APARENCIAS[self.aparencia_atual]
        paleta = PALETAS[self.paleta_atual]
        self.janela_historico.configure(fg_color=visual["fundo"])
        for frame in (
            self.frame_controles_historico,
            self.frame_grafico_historico,
            self.frame_lista_historico,
        ):
            frame.configure(fg_color=visual["painel"])
        self.lbl_historico_titulo.configure(text_color=visual["texto"])
        self.lbl_historico_subtitulo.configure(
            text_color=visual["secundario"]
        )
        for rotulo in (
            self.lbl_tipo_grafico,
            self.lbl_intervalo_historico,
            self.lbl_resumo_historico,
        ):
            rotulo.configure(text_color=visual["texto"])
        for seletor in (
            self.seletor_tipo_grafico,
            self.seletor_intervalo_historico,
        ):
            seletor.configure(
                fg_color=paleta["destaque"],
                button_color=paleta["hover"],
                button_hover_color=paleta["hover"],
                dropdown_fg_color=visual["painel"],
                dropdown_hover_color=paleta["hover"],
                text_color="#FFFFFF",
            )
        self.texto_registros_historico.configure(
            fg_color=visual["entrada"], text_color=visual["texto"]
        )
        self.desenhar_grafico_historico()

    def abrir_estatisticas(self):
        if (
            self.janela_estatisticas is not None
            and self.janela_estatisticas.winfo_exists()
        ):
            self.janela_estatisticas.lift()
            self.janela_estatisticas.focus_force()
            return

        self.registrar_historico(gravar=False)
        janela = ctk.CTkToplevel(self)
        janela.title("Estatísticas - Calculadora de Saída")
        janela.geometry("820x650")
        janela.minsize(720, 590)
        janela.transient(self)
        janela.protocol("WM_DELETE_WINDOW", self.fechar_estatisticas)
        janela.grid_columnconfigure(0, weight=1)
        janela.grid_rowconfigure(2, weight=1)
        self.janela_estatisticas = janela

        self.lbl_estatisticas_titulo = ctk.CTkLabel(
            janela, text="Estatísticas", font=("Segoe UI", 24, "bold")
        )
        self.lbl_estatisticas_titulo.grid(
            row=0, column=0, padx=24, pady=(20, 2)
        )
        self.lbl_estatisticas_mes = ctk.CTkLabel(
            janela, text="", font=("Segoe UI", 13)
        )
        self.lbl_estatisticas_mes.grid(
            row=1, column=0, padx=24, pady=(0, 14)
        )

        self.frame_cards_estatisticas = ctk.CTkFrame(
            janela, fg_color="transparent"
        )
        self.frame_cards_estatisticas.grid(
            row=2, column=0, padx=24, pady=(0, 14), sticky="nsew"
        )
        for coluna in range(2):
            self.frame_cards_estatisticas.grid_columnconfigure(
                coluna, weight=1, uniform="cards"
            )
        for linha in range(3):
            self.frame_cards_estatisticas.grid_rowconfigure(
                linha, weight=1, uniform="cards"
            )

        definicoes = (
            ("extras", "Horas extras neste mês", 0, 0),
            ("devidas", "Horas devidas neste mês", 0, 1),
            ("saldo", "Saldo total do período", 1, 0),
            ("dias", "Dias registrados", 1, 1),
            ("media", "Média diária", 2, 0),
            ("melhor", "Melhor dia do mês", 2, 1),
        )
        self.cards_estatisticas = {}
        for chave, titulo, linha, coluna in definicoes:
            self.criar_card_estatistica(chave, titulo, linha, coluna)

        self.frame_nota_estatisticas = ctk.CTkFrame(
            janela, corner_radius=14
        )
        self.frame_nota_estatisticas.grid(
            row=3, column=0, padx=24, pady=(0, 20), sticky="ew"
        )
        self.lbl_nota_estatisticas = ctk.CTkLabel(
            self.frame_nota_estatisticas,
            text="",
            font=("Segoe UI", 12),
            wraplength=730,
            justify="left",
        )
        self.lbl_nota_estatisticas.pack(
            anchor="w", padx=16, pady=12
        )

        self.aplicar_tema_janela_estatisticas()
        self.atualizar_pagina_estatisticas()
        janela.after(100, janela.focus_force)

    def criar_card_estatistica(self, chave, titulo, linha, coluna):
        frame = ctk.CTkFrame(
            self.frame_cards_estatisticas, corner_radius=16
        )
        frame.grid(
            row=linha,
            column=coluna,
            padx=(0, 7) if coluna == 0 else (7, 0),
            pady=7,
            sticky="nsew",
        )
        frame.grid_columnconfigure(0, weight=1)
        titulo_label = ctk.CTkLabel(
            frame, text=titulo, font=("Segoe UI", 13, "bold")
        )
        titulo_label.grid(
            row=0, column=0, padx=18, pady=(16, 4), sticky="w"
        )
        valor_label = ctk.CTkLabel(
            frame, text="—", font=("Segoe UI", 25, "bold")
        )
        valor_label.grid(
            row=1, column=0, padx=18, pady=(0, 3), sticky="w"
        )
        detalhe_label = ctk.CTkLabel(
            frame, text="", font=("Segoe UI", 11)
        )
        detalhe_label.grid(
            row=2, column=0, padx=18, pady=(0, 15), sticky="w"
        )
        self.cards_estatisticas[chave] = {
            "frame": frame,
            "titulo": titulo_label,
            "valor": valor_label,
            "detalhe": detalhe_label,
        }

    def fechar_estatisticas(self):
        if (
            self.janela_estatisticas is not None
            and self.janela_estatisticas.winfo_exists()
        ):
            self.janela_estatisticas.destroy()
        self.janela_estatisticas = None
        self.cards_estatisticas = {}

    @staticmethod
    def texto_dia_estatistica(registro):
        if registro is None:
            return "Sem registros"
        data = datetime.fromisoformat(registro["data"]).strftime("%d/%m")
        saldo = formatar_duracao(
            registro["saldo_segundos"], com_sinal=True
        )
        return f"{data} · {saldo}"

    def atualizar_pagina_estatisticas(self):
        if (
            self.janela_estatisticas is None
            or not self.janela_estatisticas.winfo_exists()
        ):
            return
        agora = datetime.now()
        resumo = calcular_estatisticas(self.historico, agora)
        self.lbl_estatisticas_mes.configure(
            text=f"Resumo de {MESES[agora.month - 1]} de {agora.year}"
        )
        valores = {
            "extras": (
                formatar_duracao(resumo["horas_extras_segundos"]),
                f"{resumo['dias_positivos']} dias com saldo positivo",
            ),
            "devidas": (
                formatar_duracao(resumo["horas_devidas_segundos"]),
                f"{resumo['dias_negativos']} dias com saldo negativo",
            ),
            "saldo": (
                formatar_duracao(resumo["saldo_segundos"], True),
                "Extras menos horas devidas",
            ),
            "dias": (
                str(resumo["dias"]),
                "Um registro consolidado por dia",
            ),
            "media": (
                formatar_duracao(resumo["media_segundos"], True),
                "Saldo médio por dia registrado",
            ),
            "melhor": (
                self.texto_dia_estatistica(resumo["melhor_dia"]),
                (
                    "Menor saldo: "
                    + self.texto_dia_estatistica(resumo["pior_dia"])
                ),
            ),
        }
        for chave, (valor, detalhe) in valores.items():
            self.cards_estatisticas[chave]["valor"].configure(text=valor)
            self.cards_estatisticas[chave]["detalhe"].configure(
                text=detalhe
            )

        intervalo = self.configuracao["intervalo_historico"]
        self.lbl_nota_estatisticas.configure(
            text=(
                "O registro do dia atual é provisório: ele representa o "
                "saldo caso a jornada terminasse agora. O arquivo local é "
                f"atualizado a cada {intervalo} segundos e ao sair."
            )
        )
        self.aplicar_cores_cards_estatisticas(resumo)

    def aplicar_cores_cards_estatisticas(self, resumo=None):
        if not self.cards_estatisticas:
            return
        visual = APARENCIAS[self.aparencia_atual]
        paleta = PALETAS[self.paleta_atual]
        cores_valores = {
            "extras": "#22C55E",
            "devidas": CORES_MARCA_PADRAO["hora_extra"],
            "saldo": (
                "#22C55E"
                if resumo and resumo["saldo_segundos"] > 0
                else CORES_MARCA_PADRAO["hora_extra"]
                if resumo and resumo["saldo_segundos"] < 0
                else paleta["destaque"]
            ),
            "dias": paleta["destaque"],
            "media": paleta["destaque"],
            "melhor": paleta["marca"],
        }
        for chave, card in self.cards_estatisticas.items():
            card["frame"].configure(fg_color=visual["painel"])
            card["titulo"].configure(text_color=visual["texto"])
            card["valor"].configure(text_color=cores_valores[chave])
            card["detalhe"].configure(text_color=visual["secundario"])

    def aplicar_tema_janela_estatisticas(self):
        if (
            self.janela_estatisticas is None
            or not self.janela_estatisticas.winfo_exists()
        ):
            return
        visual = APARENCIAS[self.aparencia_atual]
        self.janela_estatisticas.configure(fg_color=visual["fundo"])
        self.lbl_estatisticas_titulo.configure(text_color=visual["texto"])
        self.lbl_estatisticas_mes.configure(
            text_color=visual["secundario"]
        )
        self.frame_nota_estatisticas.configure(
            fg_color=visual["painel"]
        )
        self.lbl_nota_estatisticas.configure(
            text_color=visual["secundario"]
        )
        resumo = calcular_estatisticas(self.historico, datetime.now())
        self.aplicar_cores_cards_estatisticas(resumo)

    def abrir_sobre(self):
        if (
            self.janela_sobre is not None
            and self.janela_sobre.winfo_exists()
        ):
            self.janela_sobre.lift()
            self.janela_sobre.focus_force()
            return

        janela = ctk.CTkToplevel(self)
        janela.title("Sobre - Calculadora de Saída")
        janela.geometry("540x620")
        janela.minsize(540, 620)
        janela.resizable(False, False)
        janela.transient(self)
        janela.protocol("WM_DELETE_WINDOW", self.fechar_sobre)
        janela.grid_columnconfigure(0, weight=1)
        self.janela_sobre = janela

        try:
            icone = self.criar_imagem_bandeja()
            self.imagem_sobre = ctk.CTkImage(
                light_image=icone, dark_image=icone, size=(96, 96)
            )
        except (OSError, ValueError):
            self.imagem_sobre = None

        self.lbl_icone_sobre = ctk.CTkLabel(
            janela, text="", image=self.imagem_sobre
        )
        self.lbl_icone_sobre.grid(
            row=0, column=0, padx=24, pady=(24, 8)
        )
        self.lbl_sobre_titulo = ctk.CTkLabel(
            janela,
            text="Calculadora de Saída",
            font=("Segoe UI", 24, "bold"),
        )
        self.lbl_sobre_titulo.grid(row=1, column=0, padx=24, pady=0)
        self.lbl_sobre_versao = ctk.CTkLabel(
            janela,
            text=f"Versão {self.versao}",
            font=("Segoe UI", 13),
        )
        self.lbl_sobre_versao.grid(
            row=2, column=0, padx=24, pady=(3, 16)
        )
        self.lbl_sobre_descricao = ctk.CTkLabel(
            janela,
            text=(
                "Calcule sua jornada e acompanhe o saldo de horas\n"
                "sem interromper o seu trabalho."
            ),
            font=("Segoe UI", 13),
            justify="center",
        )
        self.lbl_sobre_descricao.grid(
            row=3, column=0, padx=24, pady=(0, 18)
        )

        self.frame_contribuidores_sobre = ctk.CTkFrame(
            janela, corner_radius=16
        )
        self.frame_contribuidores_sobre.grid(
            row=4, column=0, padx=30, pady=(0, 16), sticky="ew"
        )
        self.frame_contribuidores_sobre.grid_columnconfigure(0, weight=1)
        self.lbl_contribuidores_sobre = ctk.CTkLabel(
            self.frame_contribuidores_sobre,
            text="Contribuidores",
            font=("Segoe UI", 16, "bold"),
        )
        self.lbl_contribuidores_sobre.grid(
            row=0, column=0, columnspan=2, padx=16, pady=(16, 8)
        )
        self.linhas_contribuidores_sobre = []
        for indice, contribuidor in enumerate(CONTRIBUIDORES, start=1):
            nome = ctk.CTkLabel(
                self.frame_contribuidores_sobre,
                text=contribuidor["nome"],
                font=("Segoe UI", 13),
            )
            nome.grid(
                row=indice,
                column=0,
                padx=(18, 8),
                pady=7,
                sticky="w",
            )
            botao = ctk.CTkButton(
                self.frame_contribuidores_sobre,
                text=f"@{contribuidor['usuario']}",
                width=150,
                height=30,
                command=lambda url=contribuidor["url"]: webbrowser.open(url),
            )
            botao.grid(
                row=indice,
                column=1,
                padx=(8, 18),
                pady=7,
                sticky="e",
            )
            self.linhas_contribuidores_sobre.append((nome, botao))

        self.botao_repositorio_sobre = ctk.CTkButton(
            janela,
            text="Abrir repositório no GitHub",
            command=lambda: webbrowser.open(
                "https://github.com/lucasfhs/calculo_ponto"
            ),
            height=34,
        )
        self.botao_repositorio_sobre.grid(
            row=5, column=0, padx=30, pady=(0, 12), sticky="ew"
        )
        self.lbl_sobre_rodape = ctk.CTkLabel(
            janela,
            text="Feito por PisJuliano e contribuidores.",
            font=("Segoe UI", 11),
        )
        self.lbl_sobre_rodape.grid(
            row=6, column=0, padx=24, pady=(0, 20)
        )

        self.aplicar_tema_janela_sobre()
        janela.after(100, janela.focus_force)

    def fechar_sobre(self):
        if (
            self.janela_sobre is not None
            and self.janela_sobre.winfo_exists()
        ):
            self.janela_sobre.destroy()
        self.janela_sobre = None
        self.imagem_sobre = None

    def aplicar_tema_janela_sobre(self):
        if (
            self.janela_sobre is None
            or not self.janela_sobre.winfo_exists()
        ):
            return
        visual = APARENCIAS[self.aparencia_atual]
        paleta = PALETAS[self.paleta_atual]
        self.janela_sobre.configure(fg_color=visual["fundo"])
        self.frame_contribuidores_sobre.configure(
            fg_color=visual["painel"]
        )
        for rotulo in (
            self.lbl_sobre_titulo,
            self.lbl_contribuidores_sobre,
        ):
            rotulo.configure(text_color=visual["texto"])
        for rotulo in (
            self.lbl_sobre_versao,
            self.lbl_sobre_descricao,
            self.lbl_sobre_rodape,
        ):
            rotulo.configure(text_color=visual["secundario"])
        for nome, botao in self.linhas_contribuidores_sobre:
            nome.configure(text_color=visual["texto"])
            botao.configure(
                fg_color=visual["entrada"],
                hover_color=paleta["hover"],
                border_width=1,
                border_color=paleta["destaque"],
                text_color=visual["texto"],
            )
        self.botao_repositorio_sobre.configure(
            fg_color=paleta["destaque"],
            hover_color=paleta["hover"],
            text_color="#FFFFFF",
        )

    def atualizar_paginas_dados(self):
        self.atualizar_pagina_historico()
        self.atualizar_pagina_estatisticas()

    def calcular(self, agora=None):
        agora = agora or datetime.now()
        entrada = datetime.strptime(self.entrada.get(), "%H:%M").replace(
            year=agora.year,
            month=agora.month,
            day=agora.day,
        )
        almoco = int(self.almoco.get())
        jornada = float(self.jornada.get())

        if almoco < 0 or jornada <= 0:
            raise ValueError("A jornada e o almoço precisam ser válidos.")

        saida = entrada + timedelta(hours=jornada, minutes=almoco)
        restante = saida - agora
        total_segundos = int(restante.total_seconds())
        hora_extra = total_segundos <= 0
        duracao = abs(total_segundos)
        horas, resto = divmod(duracao, 3600)
        minutos, segundos = divmod(resto, 60)

        return {
            "agora": f"Hora atual: {agora.strftime('%H:%M:%S')}",
            "saida": f"Saída prevista: {saida.strftime('%H:%M')}",
            "restante": (
                f"Hora extra: {horas:02}:{minutos:02}:{segundos:02}"
                if hora_extra
                else f"Faltam {horas:02}:{minutos:02}:{segundos:02}"
            ),
            "hora_extra": hora_extra,
            "momento": agora,
            "entrada_dt": entrada,
            "saida_dt": saida,
            "almoco_minutos": almoco,
            "jornada_horas": jornada,
            "saldo_segundos": -total_segundos,
        }

    def atualizar(self):
        try:
            dados = self.calcular()
        except (TypeError, ValueError):
            dados = {
                "agora": f"Hora atual: {datetime.now().strftime('%H:%M:%S')}",
                "saida": "Dados inválidos.",
                "restante": "",
                "hora_extra": False,
            }

        self.lbl_agora.configure(text=dados["agora"])
        self.lbl_saida.configure(text=dados["saida"])
        self.lbl_restante.configure(
            text=dados["restante"],
            text_color=(
                self.configuracao["cores_marca"]["hora_extra"]
                if dados["hora_extra"]
                else PALETAS[self.paleta_atual]["destaque"]
            ),
        )
        self.atualizar_marca_dagua(dados)
        self.after(1000, self.atualizar)

    def aplicar_aparencia(self, nome):
        if nome not in APARENCIAS:
            return
        self.aparencia_atual = nome
        self.configuracao["aparencia"] = nome
        ctk.set_appearance_mode(APARENCIAS[nome]["modo"])
        self.aplicar_tema_visual()
        self.salvar_configuracao()

    def aplicar_paleta(self, nome):
        if nome not in PALETAS:
            return
        self.paleta_atual = nome
        self.configuracao["paleta"] = nome
        self.aplicar_tema_visual()
        self.salvar_configuracao()

    def aplicar_tema_visual(self):
        visual = APARENCIAS[self.aparencia_atual]
        paleta = PALETAS[self.paleta_atual]

        self.configure(fg_color=visual["fundo"])
        self.titulo.configure(text_color=visual["texto"])

        for painel in (self.formulario, self.preferencias):
            painel.configure(fg_color=visual["painel"])

        for rotulo in self.rotulos_campos:
            rotulo.configure(text_color=visual["secundario"])

        for campo in self.entradas:
            campo.configure(
                fg_color=visual["entrada"],
                border_color=paleta["destaque"],
                text_color=visual["texto"],
            )

        for rotulo in (
            self.lbl_aparencia,
            self.lbl_paleta,
            self.lbl_atalho_marca,
        ):
            rotulo.configure(text_color=visual["texto"])

        for seletor in (self.seletor_aparencia, self.seletor_paleta):
            seletor.configure(
                fg_color=paleta["destaque"],
                button_color=paleta["hover"],
                button_hover_color=paleta["hover"],
                dropdown_fg_color=visual["painel"],
                dropdown_hover_color=paleta["hover"],
                dropdown_text_color=visual["texto"],
                text_color="#FFFFFF",
            )

        for checkbox in (self.check_marca, self.check_iniciar_windows):
            checkbox.configure(
                fg_color=paleta["destaque"],
                hover_color=paleta["hover"],
                border_color=paleta["destaque"],
                text_color=visual["texto"],
            )
        self.entrada_atalho_marca.configure(
            fg_color=visual["entrada"],
            border_color=paleta["destaque"],
            text_color=visual["texto"],
        )
        for botao in (self.botao_personalizar, self.botao_bandeja):
            botao.configure(
                fg_color=paleta["destaque"],
                hover_color=paleta["hover"],
                text_color="#FFFFFF",
            )
        self.lbl_agora.configure(text_color=visual["secundario"])
        self.lbl_saida.configure(text_color=visual["texto"])
        self.aplicar_tema_menu_paginas()

        if self.marca_dagua is not None:
            self.aplicar_estilo_marca_dagua()
        if (
            self.janela_personalizacao is not None
            and self.janela_personalizacao.winfo_exists()
        ):
            self.aplicar_tema_janela_personalizacao()
        self.aplicar_tema_janela_historico()
        self.aplicar_tema_janela_estatisticas()
        self.aplicar_tema_janela_sobre()

    def alternar_marca_dagua(self):
        self.configuracao["exibir_marca"] = self.marca_var.get()
        if self.marca_var.get():
            self.criar_marca_dagua()
        else:
            self.destruir_marca_dagua()
        self.salvar_configuracao()

    def iniciar_atalho_global(self):
        self.atalho_global = AtalhoGlobalWindows(
            lambda: self.comandos_bandeja.put("alternar_marca")
        )
        try:
            self.atalho_global.configurar(
                self.configuracao["atalho_marca"]
            )
        except OSError as erro:
            atalho = self.configuracao["atalho_marca"]
            detalhes = str(erro)
            self.after(
                250,
                lambda atalho=atalho, detalhes=detalhes: messagebox.showwarning(
                    "Atalho global",
                    (
                        f"Não foi possível ativar o atalho {atalho}.\n\n"
                        f"Detalhes: {detalhes}"
                    ),
                    parent=self,
                ),
            )

    def aplicar_atalho_marca(self, _evento=None):
        anterior = self.configuracao["atalho_marca"]
        try:
            novo = decodificar_atalho(self.atalho_marca_var.get())[0]
            if novo == anterior:
                self.atalho_marca_var.set(novo)
                return
            self.atalho_global.configurar(novo)
        except (OSError, ValueError) as erro:
            self.atalho_marca_var.set(anterior)
            try:
                self.atalho_global.configurar(anterior)
            except OSError:
                pass
            messagebox.showerror(
                "Atalho global",
                (
                    "Não foi possível usar esse atalho.\n\n"
                    f"{erro}\n\nExemplo válido: Ctrl+Alt+M"
                ),
                parent=self,
            )
            return

        self.configuracao["atalho_marca"] = novo
        self.atalho_marca_var.set(novo)
        self.salvar_configuracao()

    def alternar_inicializacao_windows(self):
        ativar = self.iniciar_windows_var.get()
        try:
            configurar_inicializacao_windows(ativar)
        except OSError as erro:
            self.iniciar_windows_var.set(not ativar)
            acao = "ativar" if ativar else "desativar"
            messagebox.showerror(
                "Inicialização com o Windows",
                (
                    f"Não foi possível {acao} a inicialização automática.\n\n"
                    f"Detalhes: {erro}"
                ),
                parent=self,
            )

    def dimensoes_marca(self):
        tamanho = self.configuracao["tamanho_fonte_marca"]
        largura = max(350, tamanho * 23)
        altura = max(105, int(tamanho * 6.2))
        largura = min(largura, max(200, self.winfo_screenwidth() - 20))
        altura = min(altura, max(100, self.winfo_screenheight() - 40))
        return largura, altura

    def limites_tela(self):
        """Retorna os limites da área virtual, incluindo monitores secundários."""
        try:
            import ctypes

            user32 = ctypes.windll.user32
            x = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            y = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
            largura = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            altura = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            if largura > 0 and altura > 0:
                return x, y, largura, altura
        except (AttributeError, OSError):
            pass
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    def posicao_marca_valida(self, largura, altura):
        posicao = self.configuracao["posicao_marca"]
        tela_x, tela_y, tela_largura, tela_altura = self.limites_tela()
        if posicao is None:
            return max(10, self.winfo_screenwidth() - largura - 30), 35

        x_maximo = tela_x + max(0, tela_largura - largura)
        y_maximo = tela_y + max(0, tela_altura - altura)
        x = min(max(tela_x, posicao[0]), x_maximo)
        y = min(max(tela_y, posicao[1]), y_maximo)
        return x, y

    @staticmethod
    def geometria_marca(largura=None, altura=None, x=0, y=0):
        prefixo = f"{largura}x{altura}" if largura is not None else ""
        posicao_x = f"+{x}" if x >= 0 else str(x)
        posicao_y = f"+{y}" if y >= 0 else str(y)
        return f"{prefixo}{posicao_x}{posicao_y}"

    def criar_marca_dagua(self):
        if self.marca_dagua is not None and self.marca_dagua.winfo_exists():
            self.marca_dagua.lift()
            return

        marca = tk.Toplevel(self)
        marca.title("Marca d'água - Calculadora de Saída")
        marca.overrideredirect(True)
        marca.attributes("-topmost", True)
        marca.attributes("-alpha", 0.82)
        marca.configure(bg=COR_TRANSPARENTE)

        try:
            marca.wm_attributes("-transparentcolor", COR_TRANSPARENTE)
            marca.wm_attributes("-toolwindow", True)
        except tk.TclError:
            pass

        largura, altura = self.dimensoes_marca()
        x, y = self.posicao_marca_valida(largura, altura)
        marca.geometry(self.geometria_marca(largura, altura, x, y))

        self.labels_marca = {
            "agora": tk.Label(
                marca,
                bg=COR_TRANSPARENTE,
                anchor="e",
                cursor="fleur",
            ),
            "saida": tk.Label(
                marca,
                bg=COR_TRANSPARENTE,
                anchor="e",
                cursor="fleur",
            ),
            "restante": tk.Label(
                marca,
                bg=COR_TRANSPARENTE,
                anchor="e",
                cursor="fleur",
            ),
        }
        for label in self.labels_marca.values():
            label.pack(fill="x", padx=12)
            label.bind("<ButtonPress-1>", self.iniciar_arraste_marca)
            label.bind("<B1-Motion>", self.arrastar_marca)
            label.bind("<ButtonRelease-1>", self.finalizar_arraste_marca)

        marca.bind("<ButtonPress-1>", self.iniciar_arraste_marca)
        marca.bind("<B1-Motion>", self.arrastar_marca)
        marca.bind("<ButtonRelease-1>", self.finalizar_arraste_marca)
        self.marca_dagua = marca
        self.aplicar_estilo_marca_dagua()

    def aplicar_estilo_marca_dagua(self):
        if self.marca_dagua is None or not self.marca_dagua.winfo_exists():
            return

        familia = self.configuracao["fonte_marca"]
        tamanho = self.configuracao["tamanho_fonte_marca"]
        cores = self.configuracao["cores_marca"]
        self.labels_marca["agora"].configure(
            font=(familia, tamanho), fg=cores["agora"]
        )
        self.labels_marca["saida"].configure(
            font=(familia, tamanho + 5, "bold"), fg=cores["saida"]
        )
        self.labels_marca["restante"].configure(
            font=(familia, tamanho + 3), fg=cores["restante"]
        )

        largura, altura = self.dimensoes_marca()
        x, y = self.posicao_marca_valida(largura, altura)
        self.marca_dagua.geometry(
            self.geometria_marca(largura, altura, x, y)
        )

    def atualizar_marca_dagua(self, dados):
        if self.marca_dagua is None:
            return
        if not self.marca_dagua.winfo_exists():
            self.marca_dagua = None
            self.labels_marca = {}
            self.marca_var.set(False)
            self.configuracao["exibir_marca"] = False
            self.salvar_configuracao()
            return

        cores = self.configuracao["cores_marca"]
        self.labels_marca["agora"].configure(text=dados["agora"])
        self.labels_marca["saida"].configure(text=dados["saida"])
        self.labels_marca["restante"].configure(
            text=dados["restante"],
            fg=cores["hora_extra"] if dados["hora_extra"] else cores["restante"],
        )
        self.marca_dagua.lift()

    def iniciar_arraste_marca(self, evento):
        if self.marca_dagua is None:
            return
        self.arraste_marca = (
            evento.x_root,
            evento.y_root,
            self.marca_dagua.winfo_x(),
            self.marca_dagua.winfo_y(),
        )

    def arrastar_marca(self, evento):
        if self.marca_dagua is None or self.arraste_marca is None:
            return
        inicio_x, inicio_y, janela_x, janela_y = self.arraste_marca
        x = janela_x + evento.x_root - inicio_x
        y = janela_y + evento.y_root - inicio_y
        largura, altura = self.dimensoes_marca()
        tela_x, tela_y, tela_largura, tela_altura = self.limites_tela()
        x = min(max(tela_x, x), tela_x + max(0, tela_largura - largura))
        y = min(max(tela_y, y), tela_y + max(0, tela_altura - altura))
        self.marca_dagua.geometry(self.geometria_marca(x=x, y=y))

    def finalizar_arraste_marca(self, _evento):
        if self.marca_dagua is None or self.arraste_marca is None:
            return
        self.configuracao["posicao_marca"] = [
            self.marca_dagua.winfo_x(),
            self.marca_dagua.winfo_y(),
        ]
        self.arraste_marca = None
        self.salvar_configuracao()

    def abrir_personalizacao_marca(self):
        if (
            self.janela_personalizacao is not None
            and self.janela_personalizacao.winfo_exists()
        ):
            self.janela_personalizacao.lift()
            self.janela_personalizacao.focus_force()
            return

        janela = ctk.CTkToplevel(self)
        janela.title("Personalizar marca d'água")
        janela.geometry("440x560")
        janela.minsize(440, 560)
        janela.resizable(False, False)
        janela.transient(self)
        janela.protocol("WM_DELETE_WINDOW", self.fechar_personalizacao_marca)
        janela.grid_columnconfigure(1, weight=1)
        self.janela_personalizacao = janela

        self.lbl_personalizacao_titulo = ctk.CTkLabel(
            janela,
            text="Marca d'água",
            font=("Segoe UI", 22, "bold"),
        )
        self.lbl_personalizacao_titulo.grid(
            row=0, column=0, columnspan=2, padx=20, pady=(18, 4)
        )
        self.lbl_instrucao_arraste = ctk.CTkLabel(
            janela,
            text="Arraste qualquer texto da marca d'água para movê-la.",
            font=("Segoe UI", 12),
        )
        self.lbl_instrucao_arraste.grid(
            row=1, column=0, columnspan=2, padx=20, pady=(0, 16)
        )

        self.lbl_fonte = ctk.CTkLabel(
            janela, text="Fonte", font=("Segoe UI", 13, "bold")
        )
        self.lbl_fonte.grid(row=2, column=0, padx=(20, 8), pady=7, sticky="w")

        try:
            fontes = sorted(set(tkfont.families(self)), key=str.casefold)
        except tk.TclError:
            fontes = ["Arial", "Consolas", "Segoe UI"]
        if self.fonte_marca_var.get() not in fontes:
            fontes.insert(0, self.fonte_marca_var.get())

        self.combo_fonte = ctk.CTkComboBox(
            janela,
            values=fontes,
            variable=self.fonte_marca_var,
            command=self.alterar_fonte_marca,
            width=245,
        )
        self.combo_fonte.grid(
            row=2, column=1, padx=(8, 20), pady=7, sticky="ew"
        )
        self.combo_fonte.bind("<Return>", self.confirmar_fonte_digitada)
        self.combo_fonte.bind("<FocusOut>", self.confirmar_fonte_digitada)

        self.lbl_tamanho = ctk.CTkLabel(
            janela, text="Tamanho", font=("Segoe UI", 13, "bold")
        )
        self.lbl_tamanho.grid(
            row=3, column=0, padx=(20, 8), pady=7, sticky="w"
        )
        frame_tamanho = ctk.CTkFrame(janela, fg_color="transparent")
        frame_tamanho.grid(
            row=3, column=1, padx=(8, 20), pady=7, sticky="ew"
        )
        frame_tamanho.grid_columnconfigure(0, weight=1)
        self.slider_tamanho = ctk.CTkSlider(
            frame_tamanho,
            from_=9,
            to=36,
            number_of_steps=27,
            command=self.alterar_tamanho_marca,
        )
        self.slider_tamanho.set(self.configuracao["tamanho_fonte_marca"])
        self.slider_tamanho.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.lbl_valor_tamanho = ctk.CTkLabel(
            frame_tamanho,
            text=str(self.configuracao["tamanho_fonte_marca"]),
            width=28,
        )
        self.lbl_valor_tamanho.grid(row=0, column=1)

        self.lbl_cores = ctk.CTkLabel(
            janela,
            text="Cores de cada informação",
            font=("Segoe UI", 15, "bold"),
        )
        self.lbl_cores.grid(
            row=4, column=0, columnspan=2, padx=20, pady=(18, 7), sticky="w"
        )

        for indice, (chave, nome) in enumerate(NOMES_CORES.items(), start=5):
            rotulo = ctk.CTkLabel(janela, text=nome, font=("Segoe UI", 13))
            rotulo.grid(
                row=indice, column=0, padx=(20, 8), pady=6, sticky="w"
            )
            botao = ctk.CTkButton(
                janela,
                text=self.configuracao["cores_marca"][chave],
                command=lambda item=chave: self.escolher_cor_marca(item),
                height=30,
            )
            botao.grid(
                row=indice, column=1, padx=(8, 20), pady=6, sticky="ew"
            )
            self.botoes_cores[chave] = botao

        self.botao_cores_paleta = ctk.CTkButton(
            janela,
            text="Restaurar cores da paleta",
            command=self.restaurar_cores_marca,
            height=32,
        )
        self.botao_cores_paleta.grid(
            row=9, column=0, columnspan=2, padx=20, pady=(14, 6), sticky="ew"
        )
        self.botao_fechar_personalizacao = ctk.CTkButton(
            janela,
            text="Concluído",
            command=self.fechar_personalizacao_marca,
            height=34,
        )
        self.botao_fechar_personalizacao.grid(
            row=10, column=0, columnspan=2, padx=20, pady=(6, 18), sticky="ew"
        )

        self.aplicar_tema_janela_personalizacao()
        janela.after(100, janela.focus_force)

    def aplicar_tema_janela_personalizacao(self):
        if self.janela_personalizacao is None:
            return
        visual = APARENCIAS[self.aparencia_atual]
        paleta = PALETAS[self.paleta_atual]
        self.janela_personalizacao.configure(fg_color=visual["fundo"])

        for rotulo in (
            self.lbl_personalizacao_titulo,
            self.lbl_fonte,
            self.lbl_tamanho,
            self.lbl_cores,
        ):
            rotulo.configure(text_color=visual["texto"])
        self.lbl_instrucao_arraste.configure(text_color=visual["secundario"])

        self.combo_fonte.configure(
            fg_color=visual["entrada"],
            border_color=paleta["destaque"],
            button_color=paleta["destaque"],
            button_hover_color=paleta["hover"],
            dropdown_fg_color=visual["painel"],
            dropdown_hover_color=paleta["hover"],
            text_color=visual["texto"],
        )
        self.slider_tamanho.configure(
            button_color=paleta["destaque"],
            button_hover_color=paleta["hover"],
            progress_color=paleta["destaque"],
        )
        self.botao_cores_paleta.configure(
            fg_color=visual["painel"],
            hover_color=visual["entrada"],
            border_width=1,
            border_color=paleta["destaque"],
            text_color=visual["texto"],
        )
        self.botao_fechar_personalizacao.configure(
            fg_color=paleta["destaque"],
            hover_color=paleta["hover"],
            text_color="#FFFFFF",
        )
        for chave in self.botoes_cores:
            self.atualizar_botao_cor(chave)

    def alterar_fonte_marca(self, familia):
        familia = familia.strip()
        if not familia:
            return
        self.configuracao["fonte_marca"] = familia
        self.fonte_marca_var.set(familia)
        self.aplicar_estilo_marca_dagua()
        self.salvar_configuracao()

    def confirmar_fonte_digitada(self, _evento):
        self.alterar_fonte_marca(self.fonte_marca_var.get())

    def alterar_tamanho_marca(self, valor):
        tamanho = int(round(float(valor)))
        self.configuracao["tamanho_fonte_marca"] = tamanho
        self.lbl_valor_tamanho.configure(text=str(tamanho))
        self.aplicar_estilo_marca_dagua()
        self.salvar_configuracao()

    def escolher_cor_marca(self, chave):
        atual = self.configuracao["cores_marca"][chave]
        _rgb, hexadecimal = colorchooser.askcolor(
            color=atual,
            title=f"Cor: {NOMES_CORES[chave]}",
            parent=self.janela_personalizacao,
        )
        if hexadecimal is None:
            return
        self.configuracao["cores_marca"][chave] = hexadecimal.upper()
        self.atualizar_botao_cor(chave)
        self.aplicar_estilo_marca_dagua()
        self.salvar_configuracao()

    def atualizar_botao_cor(self, chave):
        if chave not in self.botoes_cores:
            return
        cor = self.configuracao["cores_marca"][chave]
        self.botoes_cores[chave].configure(
            text=cor,
            fg_color=cor,
            hover_color=cor,
            text_color=self.cor_texto_contraste(cor),
        )

    @staticmethod
    def cor_texto_contraste(cor):
        vermelho = int(cor[1:3], 16)
        verde = int(cor[3:5], 16)
        azul = int(cor[5:7], 16)
        luminosidade = (299 * vermelho + 587 * verde + 114 * azul) / 1000
        return "#111827" if luminosidade > 155 else "#FFFFFF"

    def restaurar_cores_marca(self):
        paleta = PALETAS[self.paleta_atual]
        visual = APARENCIAS[self.aparencia_atual]
        secundario = visual["secundario"]
        if isinstance(secundario, tuple):
            secundario = secundario[
                0 if ctk.get_appearance_mode().lower() == "light" else 1
            ]
        self.configuracao["cores_marca"] = {
            "agora": secundario,
            "saida": paleta["marca"],
            "restante": paleta["marca"],
            "hora_extra": CORES_MARCA_PADRAO["hora_extra"],
        }
        for chave in self.botoes_cores:
            self.atualizar_botao_cor(chave)
        self.aplicar_estilo_marca_dagua()
        self.salvar_configuracao()

    def fechar_personalizacao_marca(self):
        if (
            self.janela_personalizacao is not None
            and self.janela_personalizacao.winfo_exists()
        ):
            self.janela_personalizacao.destroy()
        self.janela_personalizacao = None
        self.botoes_cores = {}

    def criar_imagem_bandeja(self):
        try:
            with Image.open(caminho_recurso(os.path.join("assets", "clock.png"))) as imagem:
                return imagem.convert("RGBA").resize((64, 64)).copy()
        except (OSError, ValueError):
            imagem = Image.new("RGBA", (64, 64), (15, 23, 42, 255))
            desenho = ImageDraw.Draw(imagem)
            desenho.ellipse(
                (6, 6, 58, 58),
                fill=(37, 99, 235, 255),
                outline=(248, 250, 252, 255),
                width=4,
            )
            desenho.line(
                (32, 32, 32, 16),
                fill=(248, 250, 252, 255),
                width=4,
            )
            desenho.line(
                (32, 32, 44, 39),
                fill=(248, 250, 252, 255),
                width=4,
            )
            return imagem

    def iniciar_bandeja(self):
        if os.getenv("CALCULO_PONTO_SEM_BANDEJA") == "1":
            return

        menu = pystray.Menu(
            pystray.MenuItem(
                "Abrir",
                lambda _icone, _item: self.comandos_bandeja.put("abrir"),
                default=True,
            ),
            pystray.MenuItem(
                "Alternar marca d'água",
                lambda _icone, _item: self.comandos_bandeja.put(
                    "alternar_marca"
                ),
            ),
            pystray.MenuItem(
                "Sair",
                lambda _icone, _item: self.comandos_bandeja.put("sair"),
            ),
        )
        try:
            self.icone_bandeja = pystray.Icon(
                "calculo-ponto",
                self.criar_imagem_bandeja(),
                "Calculadora de Saída",
                menu,
            )
            self.icone_bandeja.run_detached()
        except (OSError, RuntimeError):
            self.icone_bandeja = None

    def processar_comandos_bandeja(self):
        if self.encerrando:
            return
        try:
            while True:
                comando = self.comandos_bandeja.get_nowait()
                if comando == "abrir":
                    self.mostrar_janela()
                elif comando == "alternar_marca":
                    self.marca_var.set(not self.marca_var.get())
                    self.alternar_marca_dagua()
                elif comando == "sair":
                    self.fechar()
                    return
        except queue.Empty:
            pass
        self.after(100, self.processar_comandos_bandeja)

    def ocultar_na_bandeja(self):
        if self.icone_bandeja is None:
            self.fechar()
            return
        self.fechar_menu_paginas()
        self.fechar_personalizacao_marca()
        self.fechar_historico()
        self.fechar_estatisticas()
        self.fechar_sobre()
        self.withdraw()

    def mostrar_janela(self):
        if self.encerrando:
            return
        self.deiconify()
        self.state("normal")
        self.lift()
        self.after(50, self.focus_force)

    def destruir_marca_dagua(self):
        if self.marca_dagua is not None and self.marca_dagua.winfo_exists():
            self.marca_dagua.destroy()
        self.marca_dagua = None
        self.labels_marca = {}
        self.arraste_marca = None

    def salvar_configuracao(self):
        try:
            caminho = caminho_configuracao()
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            temporario = f"{caminho}.tmp"
            with open(temporario, "w", encoding="utf-8") as arquivo:
                json.dump(
                    self.configuracao,
                    arquivo,
                    ensure_ascii=False,
                    indent=2,
                )
            os.replace(temporario, caminho)
        except OSError:
            pass

    def fechar(self):
        if self.encerrando:
            return
        self.encerrando = True
        if self.historico_after_id is not None:
            try:
                self.after_cancel(self.historico_after_id)
            except (tk.TclError, ValueError):
                pass
            self.historico_after_id = None
        self.registrar_historico()
        self.salvar_configuracao()
        if self.atalho_global is not None:
            self.atalho_global.parar()
            self.atalho_global = None
        if self.icone_bandeja is not None:
            self.icone_bandeja.stop()
            self.icone_bandeja = None
        self.fechar_menu_paginas()
        self.fechar_personalizacao_marca()
        self.fechar_historico()
        self.fechar_estatisticas()
        self.fechar_sobre()
        self.destruir_marca_dagua()
        self.destroy()


if __name__ == "__main__":
    app = CalculadoraSaida()
    app.mainloop()
