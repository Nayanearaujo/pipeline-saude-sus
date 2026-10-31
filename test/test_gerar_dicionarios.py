"""
Testes de gerar_dicionarios.py: a leitura de municipios da API oficial do IBGE.

Mocka a resposta da API (sem internet) e confere o parse. Testa tambem o
fallback: quando a API falha, gerar_municipios cai no modo neutro e ainda grava
o arquivo. Nunca acessa a rede nem data/raw real.
"""
import io
import json

import pandas as pd
import pytest

import gerar_dicionarios as gd


class _RespostaFake:
    """Simula o objeto de contexto devolvido por urllib.request.urlopen."""
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._payload


def test_le_municipios_da_api_ibge(monkeypatch):
    """_municipios_da_api_ibge parseia o JSON: id de 7 digitos vira codigo de 6, UF do prefixo."""
    payload = json.dumps([
        {"id": 3304557, "nome": "Rio de Janeiro"},
        {"id": 3550308, "nome": "São Paulo"},
    ]).encode("utf-8")
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda url, timeout=0: _RespostaFake(payload)
    )
    df = gd._municipios_da_api_ibge()
    linha_rj = df[df["codigo"] == "330455"].iloc[0]
    assert linha_rj["municipio"] == "Rio de Janeiro"
    assert linha_rj["uf"] == "RJ"
    assert df[df["codigo"] == "355030"].iloc[0]["uf"] == "SP"


def test_api_vazia_levanta_erro(monkeypatch):
    """Resposta vazia da API deve levantar erro (para o chamador cair no fallback)."""
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda url, timeout=0: _RespostaFake(b"[]")
    )
    with pytest.raises(ValueError):
        gd._municipios_da_api_ibge()


def test_gerar_municipios_cai_no_neutro_sem_rede(tmp_path, monkeypatch):
    """Sem API e sem CSV, gerar_municipios grava nomes neutros e nao quebra."""
    read_csv_real = pd.read_csv

    def _falha_api(*a, **k):
        raise OSError("sem rede")

    def _falha_so_url(path, *a, **k):
        # falha ao baixar o espelho (URL http); le normal um arquivo local
        if str(path).startswith("http"):
            raise OSError("sem rede")
        return read_csv_real(path, *a, **k)

    monkeypatch.setattr(gd, "_municipios_da_api_ibge", _falha_api)
    monkeypatch.setattr(pd, "read_csv", _falha_so_url)
    monkeypatch.setattr(gd, "RAW", tmp_path)
    gd.gerar_municipios({"330455", "355030"})
    saida = read_csv_real(tmp_path / "municipios.csv", dtype=str)
    assert set(saida.columns) == {"codigo", "municipio", "uf"}
    assert saida["municipio"].str.startswith("Municipio").all()
