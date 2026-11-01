"""
Testes de pipeline/qualidade.py: as regras de qualidade de dados.

Monta um banco minimo (bronze + prata + ouro) coerente entre si e confere que
todas as regras passam. Depois sabota uma tabela (soma que nao fecha) e confere
que o modulo encerra com erro. Dado inventado, nunca o banco real.
"""
import duckdb
import pytest

from pipeline import db, qualidade


def _banco_coerente(banco):
    """bronze/prata/ouro minimos, com os totais batendo entre si."""
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA bronze; CREATE SCHEMA prata; CREATE SCHEMA ouro")
    # bronze: 3 linhas; prata: 3 (nada removido)
    con.execute("CREATE TABLE bronze.internacoes AS SELECT * FROM range(3)")
    con.execute("""
        CREATE TABLE prata.internacoes AS SELECT * FROM (VALUES
            ('a1','RJ',40), ('a2','SP',0), ('a3','SP',102)
        ) AS t(aih, uf, idade)
    """)
    # dicionarios com chave unica (regras de unicidade)
    con.execute("CREATE TABLE prata.cid10 AS SELECT * FROM (VALUES ('A001','Colera')) AS t(cid, doenca)")
    con.execute(
        "CREATE TABLE prata.municipios AS SELECT * FROM "
        "(VALUES ('330455','Rio','RJ')) AS t(cod_municipio, municipio, uf)"
    )
    # ouro: totais coerentes (3 internacoes, 2 UFs)
    con.execute("CREATE TABLE ouro.kpis_gerais AS SELECT 3 AS internacoes, 1800.0 AS valor_total")
    con.execute("""
        CREATE TABLE ouro.por_estado AS SELECT * FROM (VALUES
            ('RJ', 1, 1000.0, 50.0), ('SP', 2, 800.0, 10.0)
        ) AS t(uf, internacoes, valor_total, taxa_mortalidade_pct)
    """)
    con.execute("CREATE TABLE ouro.perfil_demografico_brasil AS SELECT 3 AS internacoes")
    con.execute(
        "CREATE TABLE ouro.top_diagnosticos_brasil AS SELECT * FROM "
        "(VALUES ('A001','Colera',3)) AS t(cid, doenca, internacoes)"
    )
    # perfil e serie por UF batem com os nacionais (3 internacoes)
    con.execute("CREATE TABLE ouro.perfil_demografico AS SELECT 3 AS internacoes")
    con.execute("CREATE TABLE ouro.internacoes_diarias AS SELECT 3 AS internacoes")
    con.execute("CREATE TABLE ouro.internacoes_diarias_brasil AS SELECT 3 AS internacoes")
    con.execute("CREATE TABLE ouro.top_diagnosticos AS SELECT 1 AS x")
    # marts novos: mortalidade (obitos <= internacoes, taxa 0..100) e pareto (fecha 100%)
    con.execute(
        "CREATE TABLE ouro.mortalidade_por_cid AS "
        "SELECT 'A001' AS cid, 100 AS internacoes, 20 AS obitos, 20.0 AS taxa_mortalidade_pct"
    )
    con.execute("CREATE TABLE ouro.municipios_pareto AS "
        "SELECT '330455' AS cod_municipio, 1 AS posicao, 100.0 AS pct_acumulado")
    con.close()


def test_banco_coerente_passa(tmp_path, monkeypatch):
    banco = tmp_path / "sih.duckdb"
    _banco_coerente(banco)
    monkeypatch.setattr(db, "BANCO", banco)
    qualidade.main()  # nao deve levantar SystemExit


def test_soma_que_nao_fecha_falha(tmp_path, monkeypatch):
    banco = tmp_path / "sih.duckdb"
    _banco_coerente(banco)
    # sabota: muda o KPI para 999, quebrando 'partes somam o todo'
    con = duckdb.connect(str(banco))
    con.execute("CREATE OR REPLACE TABLE ouro.kpis_gerais AS SELECT 999 AS internacoes, 1800.0 AS valor_total")
    con.close()
    monkeypatch.setattr(db, "BANCO", banco)
    with pytest.raises(SystemExit):
        qualidade.main()


@pytest.mark.parametrize(
    ("tabela", "sql"),
    [
        ("ouro.mortalidade_por_cid", "UPDATE ouro.mortalidade_por_cid SET internacoes = 99"),
        (
            "ouro.municipios_pareto",
            "INSERT INTO ouro.municipios_pareto VALUES ('330456', 2, 90.0)",
        ),
        (
            "ouro.municipios_pareto",
            "INSERT INTO ouro.municipios_pareto VALUES ('330455', 2, 100.0)",
        ),
    ],
)
def test_qualidade_rejeita_marts_complementares_invalidos(
    tmp_path, monkeypatch, tabela, sql
):
    """Quebras reais de elegibilidade, ordem e chave precisam bloquear o build."""
    banco = tmp_path / "sih.duckdb"
    _banco_coerente(banco)
    con = duckdb.connect(str(banco))
    con.execute(sql)
    con.close()
    monkeypatch.setattr(db, "BANCO", banco)
    with pytest.raises(SystemExit):
        qualidade.main()
