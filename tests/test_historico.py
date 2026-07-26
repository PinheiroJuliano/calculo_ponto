import json
import os
import tempfile
import unittest
from datetime import date, datetime

from historico import (
    atualizar_registro,
    calcular_estatisticas,
    carregar_historico,
    formatar_duracao,
    salvar_historico,
)


def registro(data, saldo):
    return {
        "data": data,
        "entrada": "08:00",
        "almoco_minutos": 60,
        "jornada_horas": 8.0,
        "saida_prevista": "17:00",
        "saldo_segundos": saldo,
        "atualizado_em": f"{data}T18:00:00",
    }


class HistoricoTests(unittest.TestCase):
    def test_atualiza_um_unico_registro_por_dia(self):
        registros = [registro("2026-07-24", 1800)]
        atualizados = atualizar_registro(
            registros, registro("2026-07-24", 3600)
        )
        self.assertEqual(len(atualizados), 1)
        self.assertEqual(atualizados[0]["saldo_segundos"], 3600)

    def test_calcula_estatisticas_apenas_do_mes(self):
        registros = [
            registro("2026-07-01", 3600),
            registro("2026-07-02", -1800),
            registro("2026-06-30", 7200),
        ]
        resumo = calcular_estatisticas(registros, date(2026, 7, 26))
        self.assertEqual(resumo["dias"], 2)
        self.assertEqual(resumo["horas_extras_segundos"], 3600)
        self.assertEqual(resumo["horas_devidas_segundos"], 1800)
        self.assertEqual(resumo["saldo_segundos"], 1800)
        self.assertEqual(resumo["media_segundos"], 900)

    def test_salva_e_carrega_json(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "historico.json")
            esperado = [registro("2026-07-24", 900)]
            salvar_historico(
                caminho,
                esperado,
                atualizado_em=datetime(2026, 7, 24, 18, 0),
            )
            self.assertEqual(carregar_historico(caminho), esperado)
            with open(caminho, encoding="utf-8") as arquivo:
                self.assertEqual(json.load(arquivo)["versao"], 1)

    def test_ignora_arquivo_invalido(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "historico.json")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write("{ inválido")
            self.assertEqual(carregar_historico(caminho), [])

    def test_formata_duracao_com_sinal(self):
        self.assertEqual(formatar_duracao(5400, com_sinal=True), "+01h 30min")
        self.assertEqual(formatar_duracao(-900, com_sinal=True), "−00h 15min")


if __name__ == "__main__":
    unittest.main()
