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
    con.execute("""
        CREATE TABLE bronze.internacoes AS SELECT * FROM (VALUES
            ('a1', '1000.00', '20260701'),
            ('a2', '400.00', '20260701'),
            ('a3', '400.00', '20260701')
        ) AS t(N_AIH, VAL_TOT, DT_SAIDA)
    """)
    con.execute("""
        CREATE TABLE prata.internacoes AS SELECT * FROM (VALUES
            ('a1','RJ',40,1000.00,3), ('a2','SP',0,400.00,0), ('a3','SP',102,400.00,5)
        ) AS t(aih, uf, idade, valor_total, dias_permanencia)
    """)
    # dicionarios com chave unica (regras de unicidade)
    con.execute("CREATE TABLE prata.cid10 AS SELECT * FROM (VALUES ('A001','Colera')) AS t(cid, doenca)")
    con.execute(
        "CREATE TABLE prata.municipios AS SELECT * FROM "
        "(VALUES ('330455','Rio','RJ')) AS t(cod_municipio, municipio, uf)"
    )
    # ouro: totais coerentes (3 internacoes, 2 UFs)
    con.execute("CREATE TABLE ouro.kpis_gerais AS SELECT 3 AS internacoes, 1800.00 AS valor_total")
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
    con.execute("CREATE OR REPLACE TABLE ouro.kpis_gerais AS SELECT 999 AS internacoes, 1800.00 AS valor_total")
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


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE prata.internacoes SET valor_total = -1 WHERE aih = 'a1'",
        "UPDATE prata.internacoes SET valor_total = NULL WHERE aih = 'a2'",
        "UPDATE prata.internacoes SET dias_permanencia = -1 WHERE aih = 'a3'",
    ],
)
def test_qualidade_rejeita_valores_financeiros_e_permanencia_invalidos(tmp_path, monkeypatch, sql):
    """Valores negativos, pagamentos nulos e permanencias negativas nao passam."""
    banco = tmp_path / "sih.duckdb"
    _banco_coerente(banco)
    con = duckdb.connect(str(banco))
    con.execute(sql)
    con.close()
    monkeypatch.setattr(db, "BANCO", banco)
    with pytest.raises(SystemExit):
        qualidade.main()


@pytest.mark.parametrize("sql", [
    "DELETE FROM prata.internacoes WHERE aih = 'a1'",
    "UPDATE prata.internacoes SET aih = 'inexistente' WHERE aih = 'a1'",
    "UPDATE prata.internacoes SET valor_total = 1000.01 WHERE aih = 'a1'",
    "UPDATE ouro.kpis_gerais SET valor_total = 1800.01",
])
def test_reconciliacao_detecta_perda_troca_de_aih_e_divergencia_financeira(tmp_path, monkeypatch, sql):
    banco = tmp_path / "sih.duckdb"
    _banco_coerente(banco)
    with duckdb.connect(str(banco)) as con:
        con.execute(sql)
        novas_regras = [consulta for descricao, consulta in qualidade._regras(con)
                        if descricao.startswith("Reconciliacao:")]
        assert not all(con.execute(consulta).fetchone()[0] for consulta in novas_regras)
    monkeypatch.setattr(db, "BANCO", banco)
    with pytest.raises(SystemExit):
        qualidade.main()


def test_reconciliacao_aceita_exclusoes_previstas(tmp_path, monkeypatch):
    banco = tmp_path / "sih.duckdb"
    _banco_coerente(banco)
    with duckdb.connect(str(banco)) as con:
        con.execute("""
            INSERT INTO bronze.internacoes VALUES
                ('a1', '900.00', '20260101'),
                ('sem_valor', NULL, '20260701'),
                ('sem_valor', '', '20260101'),
                ('a2', NULL, '20260101')
        """)
    monkeypatch.setattr(db, "BANCO", banco)
    qualidade.main()


def test_reconciliacao_usa_desempate_financeiro_numerico(tmp_path, monkeypatch):
    banco = tmp_path / "sih.duckdb"
    _banco_coerente(banco)
    with duckdb.connect(str(banco)) as con:
        con.execute("UPDATE bronze.internacoes SET VAL_TOT = '1000.00' WHERE N_AIH = 'a1'")
        con.execute("INSERT INTO bronze.internacoes VALUES ('a1', '900.00', '20260701')")
    monkeypatch.setattr(db, "BANCO", banco)
    qualidade.main()
