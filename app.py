from datetime import datetime, timedelta
import tkinter as tk

import customtkinter as ctk


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


TEMAS = {
    "Azul": {
        "modo": "dark",
        "fundo": "#0B1120",
        "painel": "#151E31",
        "entrada": "#0F172A",
        "destaque": "#06B6D4",
        "hover": "#0891B2",
        "texto": "#F8FAFC",
        "secundario": "#94A3B8",
        "marca": "#22D3EE",
    },
    "Verde": {
        "modo": "dark",
        "fundo": "#071A12",
        "painel": "#10271C",
        "entrada": "#0A1F16",
        "destaque": "#22C55E",
        "hover": "#16A34A",
        "texto": "#F0FDF4",
        "secundario": "#86A995",
        "marca": "#4ADE80",
    },
    "Roxo": {
        "modo": "dark",
        "fundo": "#130C21",
        "painel": "#241538",
        "entrada": "#1A1029",
        "destaque": "#A855F7",
        "hover": "#9333EA",
        "texto": "#FAF5FF",
        "secundario": "#B7A2C9",
        "marca": "#C084FC",
    },
    "Âmbar": {
        "modo": "dark",
        "fundo": "#1C1407",
        "painel": "#2C2110",
        "entrada": "#211807",
        "destaque": "#F59E0B",
        "hover": "#D97706",
        "texto": "#FFFBEB",
        "secundario": "#C5AD80",
        "marca": "#FBBF24",
    },
    "Claro": {
        "modo": "light",
        "fundo": "#EAF2F8",
        "painel": "#FFFFFF",
        "entrada": "#F8FAFC",
        "destaque": "#2563EB",
        "hover": "#1D4ED8",
        "texto": "#172033",
        "secundario": "#64748B",
        "marca": "#1D4ED8",
    },
}

COR_HORA_EXTRA = "#F43F5E"
COR_TRANSPARENTE = "#010203"


class CalculadoraSaida(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Calculadora de Saída")
        self.geometry("420x590")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.fechar)

        self.marca_dagua = None
        self.labels_marca = {}
        self.tema_atual = "Azul"
        self.tema_var = tk.StringVar(value=self.tema_atual)
        self.marca_var = tk.BooleanVar(value=False)

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

        self.lbl_aparencia = ctk.CTkLabel(
            self.preferencias,
            text="Aparência",
            font=("Segoe UI", 14, "bold"),
        )
        self.lbl_aparencia.grid(row=0, column=0, padx=16, pady=(13, 7), sticky="w")

        self.seletor_tema = ctk.CTkOptionMenu(
            self.preferencias,
            values=list(TEMAS),
            variable=self.tema_var,
            command=self.aplicar_tema,
            width=135,
        )
        self.seletor_tema.grid(row=0, column=1, padx=16, pady=(13, 7), sticky="e")

        self.check_marca = ctk.CTkCheckBox(
            self.preferencias,
            text="Exibir informações como marca d'água",
            variable=self.marca_var,
            command=self.alternar_marca_dagua,
            font=("Segoe UI", 13),
        )
        self.check_marca.grid(
            row=1, column=0, columnspan=2, padx=16, pady=(7, 14), sticky="w"
        )
        self.preferencias.grid_columnconfigure(0, weight=1)

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
        self.lbl_restante.pack(pady=(7, 0))

        self.aplicar_tema(self.tema_atual)
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

    def calcular(self):
        agora = datetime.now()
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
        segundos = int(restante.total_seconds())
        hora_extra = segundos <= 0
        duracao = abs(segundos)
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
                COR_HORA_EXTRA
                if dados["hora_extra"]
                else TEMAS[self.tema_atual]["destaque"]
            ),
        )
        self.atualizar_marca_dagua(dados)
        self.after(1000, self.atualizar)

    def aplicar_tema(self, nome):
        self.tema_atual = nome
        tema = TEMAS[nome]
        ctk.set_appearance_mode(tema["modo"])

        self.configure(fg_color=tema["fundo"])
        self.titulo.configure(text_color=tema["texto"])

        for painel in (self.formulario, self.preferencias):
            painel.configure(fg_color=tema["painel"])

        for rotulo in self.rotulos_campos:
            rotulo.configure(text_color=tema["secundario"])

        for campo in self.entradas:
            campo.configure(
                fg_color=tema["entrada"],
                border_color=tema["destaque"],
                text_color=tema["texto"],
            )

        self.lbl_aparencia.configure(text_color=tema["texto"])
        self.seletor_tema.configure(
            fg_color=tema["destaque"],
            button_color=tema["hover"],
            button_hover_color=tema["hover"],
            dropdown_fg_color=tema["painel"],
            dropdown_hover_color=tema["hover"],
            dropdown_text_color=tema["texto"],
            text_color="#FFFFFF",
        )
        self.check_marca.configure(
            fg_color=tema["destaque"],
            hover_color=tema["hover"],
            border_color=tema["destaque"],
            text_color=tema["texto"],
        )
        self.lbl_agora.configure(text_color=tema["secundario"])
        self.lbl_saida.configure(text_color=tema["texto"])

        if self.marca_dagua is not None:
            self.aplicar_cor_marca_dagua()

    def alternar_marca_dagua(self):
        if self.marca_var.get():
            self.criar_marca_dagua()
        else:
            self.destruir_marca_dagua()

    def criar_marca_dagua(self):
        if self.marca_dagua is not None:
            return

        marca = tk.Toplevel(self)
        marca.title("Marca d'água - Calculadora de Saída")
        marca.overrideredirect(True)
        marca.attributes("-topmost", True)
        marca.attributes("-alpha", 0.78)
        marca.configure(bg=COR_TRANSPARENTE)

        try:
            marca.wm_attributes("-transparentcolor", COR_TRANSPARENTE)
            marca.wm_attributes("-toolwindow", True)
        except tk.TclError:
            pass

        largura, altura = 390, 105
        x = max(10, marca.winfo_screenwidth() - largura - 30)
        marca.geometry(f"{largura}x{altura}+{x}+35")

        self.labels_marca = {
            "agora": tk.Label(
                marca,
                font=("Segoe UI", 12),
                bg=COR_TRANSPARENTE,
                anchor="e",
            ),
            "saida": tk.Label(
                marca,
                font=("Segoe UI", 17, "bold"),
                bg=COR_TRANSPARENTE,
                anchor="e",
            ),
            "restante": tk.Label(
                marca,
                font=("Segoe UI", 15),
                bg=COR_TRANSPARENTE,
                anchor="e",
            ),
        }
        for label in self.labels_marca.values():
            label.pack(fill="x", padx=12)

        self.marca_dagua = marca
        self.aplicar_cor_marca_dagua()

    def aplicar_cor_marca_dagua(self):
        if self.marca_dagua is None:
            return
        tema = TEMAS[self.tema_atual]
        self.labels_marca["agora"].configure(fg=tema["secundario"])
        self.labels_marca["saida"].configure(fg=tema["marca"])

    def atualizar_marca_dagua(self, dados):
        if self.marca_dagua is None:
            return

        if not self.marca_dagua.winfo_exists():
            self.marca_dagua = None
            self.labels_marca = {}
            self.marca_var.set(False)
            return

        self.labels_marca["agora"].configure(text=dados["agora"])
        self.labels_marca["saida"].configure(text=dados["saida"])
        self.labels_marca["restante"].configure(
            text=dados["restante"],
            fg=(
                COR_HORA_EXTRA
                if dados["hora_extra"]
                else TEMAS[self.tema_atual]["marca"]
            ),
        )
        self.marca_dagua.lift()

    def destruir_marca_dagua(self):
        if self.marca_dagua is not None:
            self.marca_dagua.destroy()
        self.marca_dagua = None
        self.labels_marca = {}

    def fechar(self):
        self.destruir_marca_dagua()
        self.destroy()


if __name__ == "__main__":
    app = CalculadoraSaida()
    app.mainloop()
