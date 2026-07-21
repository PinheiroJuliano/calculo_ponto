from datetime import datetime, timedelta
import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class CalculadoraSaida(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Calculadora de Saída")
        self.geometry("360x420")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        ctk.CTkLabel(
            self,
            text="Calculadora de Saída",
            font=("Segoe UI", 24, "bold")
        ).pack(pady=5)

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", padx=20)

        ctk.CTkLabel(frame, text="Hora de entrada (HH:MM)").pack(pady=(15, 5))
        self.entrada = ctk.CTkEntry(frame)
        self.entrada.insert(0, "08:00")
        self.entrada.pack(padx=20, fill="x")

        ctk.CTkLabel(frame, text="Almoço (minutos)").pack(pady=(15, 5))
        self.almoco = ctk.CTkEntry(frame)
        self.almoco.insert(0, "60")
        self.almoco.pack(padx=20, fill="x")

        ctk.CTkLabel(frame, text="Jornada (horas)").pack(pady=(15, 5))
        self.jornada = ctk.CTkEntry(frame)
        self.jornada.insert(0, "8")
        self.jornada.pack(padx=20, fill="x")

        self.lbl_agora = ctk.CTkLabel(self, text="", font=("Segoe UI", 14))
        self.lbl_agora.pack(pady=(20, 5))

        self.lbl_saida = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 18, "bold")
        )
        self.lbl_saida.pack()

        self.lbl_restante = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 18)
        )
        self.lbl_restante.pack(pady=10)

        self.atualizar()

    def atualizar(self):

        agora = datetime.now()

        try:
            entrada = datetime.strptime(
                self.entrada.get(),
                "%H:%M"
            ).replace(
                year=agora.year,
                month=agora.month,
                day=agora.day
            )

            almoco = int(self.almoco.get())
            jornada = float(self.jornada.get())

            saida = entrada + timedelta(
                hours=jornada,
                minutes=almoco
            )

            restante = saida - agora

            self.lbl_agora.configure(
                text=f"Hora atual: {agora.strftime('%H:%M:%S')}"
            )

            self.lbl_saida.configure(
                text=f"Saída prevista: {saida.strftime('%H:%M')}"
            )

            if restante.total_seconds() > 0:

                total = int(restante.total_seconds())

                horas = total // 3600
                minutos = (total % 3600) // 60
                segundos = total % 60

                self.lbl_restante.configure(
                    text=f"Faltam {horas:02}:{minutos:02}:{segundos:02}"
                )

            else:

                extra = abs(int(restante.total_seconds()))

                horas = extra // 3600
                minutos = (extra % 3600) // 60
                segundos = extra % 60

                self.lbl_restante.configure(
                    text=f"Hora extra: {horas:02}:{minutos:02}:{segundos:02}"
                )

        except:
            self.lbl_saida.configure(text="Dados inválidos.")
            self.lbl_restante.configure(text="")

        self.after(1000, self.atualizar)


app = CalculadoraSaida()
app.mainloop()