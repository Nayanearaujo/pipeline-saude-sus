"""Testes de completude do download sem acessar o DATASUS."""

import pandas as pd
import pytest

import baixar_dados


def test_download_incompleto_nao_sobrescreve_parquet(tmp_path, monkeypatch):
    monkeypatch.setattr(baixar_dados, "RAW", tmp_path)
    monkeypatch.setattr(baixar_dados, "UFS", ["RJ", "SP"])
    monkeypatch.setattr(baixar_dados, "TODAS_UFS", ["RJ", "SP"])
    monkeypatch.delenv("PERMITIR_PARCIAL", raising=False)
    monkeypatch.setattr(
        baixar_dados, "_baixar_dbc",
        lambda nome: b"arquivo" if nome.startswith("RDRJ") else None,
    )
    monkeypatch.setattr(
        baixar_dados, "_dbc_para_df",
        lambda conteudo, nome: pd.DataFrame({"N_AIH": ["123"]}),
    )
    destino = tmp_path / "internacoes.parquet"
    destino.write_bytes(b"dataset-anterior")
    with pytest.raises(SystemExit):
        baixar_dados.main()
    assert destino.read_bytes() == b"dataset-anterior"


def test_download_parcial_exige_opt_in(tmp_path, monkeypatch):
    monkeypatch.setattr(baixar_dados, "RAW", tmp_path)
    monkeypatch.setattr(baixar_dados, "UFS", ["RJ", "SP"])
    monkeypatch.setenv("PERMITIR_PARCIAL", "1")
    monkeypatch.setattr(
        baixar_dados, "_baixar_dbc",
        lambda nome: b"arquivo" if nome.startswith("RDRJ") else None,
    )
    monkeypatch.setattr(
        baixar_dados, "_dbc_para_df",
        lambda conteudo, nome: pd.DataFrame({"N_AIH": ["123"]}),
    )
    baixar_dados.main()
    resultado = pd.read_parquet(tmp_path / "internacoes.parquet")
    assert len(resultado) == 1
    assert resultado["UF_ARQUIVO"].tolist() == ["RJ"]


def test_falha_ao_escrever_preserva_parquet_anterior(tmp_path, monkeypatch):
    """Falha de disco durante a escrita nao publica arquivo incompleto."""
    monkeypatch.setenv("PERMITIR_PARCIAL", "1")
    monkeypatch.setattr(baixar_dados, "RAW", tmp_path)
    monkeypatch.setattr(baixar_dados, "UFS", ["RJ"])
    monkeypatch.setattr(baixar_dados, "_baixar_dbc", lambda nome: b"arquivo")
    monkeypatch.setattr(
        baixar_dados, "_dbc_para_df",
        lambda conteudo, nome: pd.DataFrame({"N_AIH": ["123"]}),
    )
    destino = tmp_path / "internacoes.parquet"
    destino.write_bytes(b"versao-anterior")

    def escrita_interrompida(self, path, **kwargs):
        path.write_bytes(b"arquivo-incompleto")
        raise OSError("disco cheio")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", escrita_interrompida)
    with pytest.raises(OSError, match="disco cheio"):
        baixar_dados.main()
    assert destino.read_bytes() == b"versao-anterior"
    assert not list(tmp_path.glob(".internacoes-*.parquet"))


@pytest.mark.parametrize(
    ("ano", "mes", "ufs"),
    [
        (2026, 0, ["RJ"]),
        (2026, 13, ["RJ"]),
        (1999, 4, ["RJ"]),
        (2026, 4, []),
        (2026, 4, ["RJ", "RJ"]),
        (2026, 4, ["XX"]),
    ],
)
def test_configuracao_invalida_bloqueia_download(monkeypatch, ano, mes, ufs):
    monkeypatch.setattr(baixar_dados, "ANO", ano)
    monkeypatch.setattr(baixar_dados, "MES", mes)
    monkeypatch.setattr(baixar_dados, "UFS", ufs)

    def download_proibido(nome):
        pytest.fail("Download iniciado com configuracao invalida")

    monkeypatch.setattr(baixar_dados, "_baixar_dbc", download_proibido)
    with pytest.raises(ValueError):
        baixar_dados.main()


def test_dbc_vazio_nao_substitui_parquet(tmp_path, monkeypatch):
    monkeypatch.setattr(baixar_dados, "RAW", tmp_path)
    monkeypatch.setattr(baixar_dados, "UFS", ["RJ"])
    monkeypatch.setattr(baixar_dados, "TODAS_UFS", ["RJ"])
    monkeypatch.delenv("PERMITIR_PARCIAL", raising=False)
    monkeypatch.setattr(baixar_dados, "_baixar_dbc", lambda nome: b"arquivo")
    monkeypatch.setattr(
        baixar_dados, "_dbc_para_df", lambda conteudo, nome: pd.DataFrame({"N_AIH": []})
    )
    destino = tmp_path / "internacoes.parquet"
    destino.write_bytes(b"versao-anterior")
    with pytest.raises(SystemExit):
        baixar_dados.main()
    assert destino.read_bytes() == b"versao-anterior"


def test_subconjunto_completo_exige_opt_in_antes_do_download(tmp_path, monkeypatch):
    monkeypatch.setattr(baixar_dados, "RAW", tmp_path)
    monkeypatch.setattr(baixar_dados, "UFS", ["RJ"])
    monkeypatch.delenv("PERMITIR_PARCIAL", raising=False)

    def nao_deve_baixar(nome):
        pytest.fail("Amostra sem permissao nao pode iniciar download")

    monkeypatch.setattr(baixar_dados, "_baixar_dbc", nao_deve_baixar)
    with pytest.raises(SystemExit):
        baixar_dados.main()
    assert not (tmp_path / "internacoes.parquet").exists()


def test_subconjunto_com_opt_in_publica_amostra(tmp_path, monkeypatch):
    monkeypatch.setattr(baixar_dados, "RAW", tmp_path)
    monkeypatch.setattr(baixar_dados, "UFS", ["RJ"])
    monkeypatch.setenv("PERMITIR_PARCIAL", "1")
    monkeypatch.setattr(baixar_dados, "_baixar_dbc", lambda nome: b"arquivo")
    monkeypatch.setattr(
        baixar_dados, "_dbc_para_df",
        lambda conteudo, nome: pd.DataFrame({"N_AIH": ["123"]}),
    )
    baixar_dados.main()
    assert pd.read_parquet(tmp_path / "internacoes.parquet")["UF_ARQUIVO"].tolist() == ["RJ"]
