"""
Testes de gerar_dicionarios.py: a leitura de municipios da API oficial do IBGE.

Mocka a resposta da API (sem internet) e confere o parse. Testa tambem o
fallback: quando a API falha, gerar_municipios cai no modo neutro e ainda grava
o arquivo. Nunca acessa a rede nem data/raw real.
"""
import json

import pandas as pd
import pytest

import gerar_dicionarios as gd


class _RespostaFake:
    """Simula o objeto de contexto devolvido por urllib.request.urlopen."""
    def __init__(self, payload: bytes):
        self._payload = payload
        self.headers = {}  # sem Content-Encoding: resposta em texto puro

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


def test_cid_combina_categorias_e_subcategorias(tmp_path, monkeypatch):
    def fonte(url, **kwargs):
        if url == gd.URL_CID_CATEGORIAS:
            return pd.DataFrame({'CAT': ['A00', 'A00'], 'DESCRICAO': ['Categoria', 'Duplicada']})
        return pd.DataFrame({'SUBCAT': ['A00.1'], 'DESCRICAO': ['Subcategoria']})
    monkeypatch.setattr(pd, 'read_csv', fonte)
    monkeypatch.setattr(gd, 'RAW', tmp_path)
    gd.gerar_cid({'A00', 'A001', 'ZZZ'})
    import csv
    with (tmp_path / 'cid10.csv').open() as f:
        linhas = list(csv.DictReader(f))
    assert linhas == [{'codigo': 'A00', 'descricao': 'Categoria'},
                      {'codigo': 'A001', 'descricao': 'Subcategoria'}]


def test_cid_sem_rede_publica_fallback_identificado(tmp_path, monkeypatch):
    monkeypatch.setattr(gd, 'RAW', tmp_path)
    monkeypatch.setattr(pd, 'read_csv', lambda *a, **k: (_ for _ in ()).throw(OSError('sem rede')))
    gd.gerar_cid({'A00', 'A001', '', 'nan'})
    import csv
    with (tmp_path / 'cid10.csv').open() as f:
        linhas = list(csv.DictReader(f))
    assert {x['descricao'] for x in linhas} == {'CID A00', 'CID A001'}


def test_municipios_api_e_espelho(tmp_path, monkeypatch):
    monkeypatch.setattr(gd, 'RAW', tmp_path)
    monkeypatch.setattr(gd, '_municipios_da_api_ibge', lambda: pd.DataFrame({
        'codigo': ['330455'], 'municipio': ['Rio'], 'uf': ['RJ']}))
    gd.gerar_municipios({'330455'})
    assert pd.read_csv(tmp_path / 'municipios.csv').municipio.tolist() == ['Rio']
    monkeypatch.setattr(gd, '_municipios_da_api_ibge', lambda: (_ for _ in ()).throw(OSError('offline')))
    leitura = pd.read_csv
    monkeypatch.setattr(pd, 'read_csv', lambda *a, **k: pd.DataFrame({
        'codigo_ibge': ['3304557', '3304557'], 'nome': ['Rio', 'Rio']}))
    gd.gerar_municipios({'330455'})
    assert len(leitura(tmp_path / 'municipios.csv')) == 1


def test_api_gzip_e_coluna_invalida(monkeypatch):
    import gzip
    resposta = _RespostaFake(gzip.compress(json.dumps([{'id': 3550308, 'nome': 'São Paulo'}]).encode()))
    resposta.headers = {'Content-Encoding': 'gzip'}
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: resposta)
    assert gd._municipios_da_api_ibge().municipio.tolist() == ['São Paulo']
    with pytest.raises(KeyError):
        gd._coluna(pd.DataFrame({'outra': []}), 'codigo')


def test_main_dicionarios_exige_parquet_e_encaminha_codigos(tmp_path, monkeypatch):
    parquet = tmp_path / 'fonte.parquet'
    monkeypatch.setattr(gd, 'PARQUET', parquet)
    with pytest.raises(SystemExit):
        gd.main()
    pd.DataFrame({'MUNIC_RES': ['3304557'], 'DIAG_PRINC': ['A00']}).to_parquet(parquet)
    chamados = []
    monkeypatch.setattr(gd, 'gerar_municipios', lambda cod: chamados.append(cod))
    monkeypatch.setattr(gd, 'gerar_cid', lambda cod: chamados.append(cod))
    gd.main()
    assert chamados == [{'330455'}, {'A00'}]
