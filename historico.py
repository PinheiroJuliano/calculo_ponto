"""Persistência e estatísticas do histórico diário da calculadora."""

from copy import deepcopy
from datetime import date, datetime
import json
import os


VERSAO_HISTORICO = 1


def carregar_historico(caminho):
    """Carrega e normaliza os registros válidos de um arquivo JSON."""
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)
    except (OSError, ValueError, TypeError):
        return []

    registros = (
        conteudo.get("registros", [])
        if isinstance(conteudo, dict)
        else conteudo
    )
    if not isinstance(registros, list):
        return []

    por_data = {}
    for item in registros:
        normalizado = normalizar_registro(item)
        if normalizado is not None:
            por_data[normalizado["data"]] = normalizado
    return [por_data[chave] for chave in sorted(por_data)]


def normalizar_registro(registro):
    if not isinstance(registro, dict):
        return None
    try:
        data_registro = date.fromisoformat(registro["data"]).isoformat()
        saldo = int(registro["saldo_segundos"])
        almoco = int(registro["almoco_minutos"])
        jornada = float(registro["jornada_horas"])
        entrada = str(registro["entrada"])
        saida = str(registro["saida_prevista"])
        atualizado_em = str(registro["atualizado_em"])
    except (KeyError, TypeError, ValueError):
        return None

    if almoco < 0 or jornada <= 0:
        return None
    return {
        "data": data_registro,
        "entrada": entrada,
        "almoco_minutos": almoco,
        "jornada_horas": jornada,
        "saida_prevista": saida,
        "saldo_segundos": saldo,
        "atualizado_em": atualizado_em,
    }


def atualizar_registro(registros, registro):
    """Insere ou substitui o registro do mesmo dia."""
    normalizado = normalizar_registro(registro)
    if normalizado is None:
        raise ValueError("Registro de histórico inválido.")

    por_data = {
        item["data"]: deepcopy(item)
        for item in registros
        if normalizar_registro(item) is not None
    }
    por_data[normalizado["data"]] = normalizado
    return [por_data[chave] for chave in sorted(por_data)]


def salvar_historico(caminho, registros, atualizado_em=None):
    """Grava o histórico de forma atômica."""
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    instante = atualizado_em or datetime.now()
    conteudo = {
        "versao": VERSAO_HISTORICO,
        "atualizado_em": instante.isoformat(timespec="seconds"),
        "registros": registros,
    }
    temporario = f"{caminho}.tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, caminho)


def filtrar_mes(registros, referencia=None):
    referencia = referencia or date.today()
    if isinstance(referencia, datetime):
        referencia = referencia.date()
    prefixo = referencia.strftime("%Y-%m-")
    return [
        item
        for item in registros
        if isinstance(item, dict)
        and str(item.get("data", "")).startswith(prefixo)
    ]


def calcular_estatisticas(registros, referencia=None):
    """Resume horas extras, débitos e saldo do mês da referência."""
    mensais = filtrar_mes(registros, referencia)
    saldos = [int(item["saldo_segundos"]) for item in mensais]
    extras = sum(valor for valor in saldos if valor > 0)
    debitos = abs(sum(valor for valor in saldos if valor < 0))
    saldo = sum(saldos)
    melhor = max(mensais, key=lambda item: item["saldo_segundos"], default=None)
    pior = min(mensais, key=lambda item: item["saldo_segundos"], default=None)

    return {
        "registros": mensais,
        "dias": len(mensais),
        "dias_positivos": sum(valor > 0 for valor in saldos),
        "dias_negativos": sum(valor < 0 for valor in saldos),
        "horas_extras_segundos": extras,
        "horas_devidas_segundos": debitos,
        "saldo_segundos": saldo,
        "media_segundos": int(saldo / len(saldos)) if saldos else 0,
        "melhor_dia": melhor,
        "pior_dia": pior,
    }


def formatar_duracao(segundos, com_sinal=False):
    segundos = int(segundos)
    sinal = ""
    if com_sinal:
        sinal = "+" if segundos > 0 else "−" if segundos < 0 else ""
    minutos_totais = abs(segundos) // 60
    horas, minutos = divmod(minutos_totais, 60)
    return f"{sinal}{horas:02}h {minutos:02}min"
