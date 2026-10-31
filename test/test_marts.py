"""
Testes de pipeline/marts.py (executor) e dos marts ouro 01 e 02 em SQL.

O executor roda sobre uma pasta de marts inventada; os marts 01 e 02 rodam
sobre uma prata minima montada a mao, para provar as regras com entrada conhecida.
"""
from pathlib import Path

import duckdb
import pytest

from pipeline import db, marts


def _prata_minima(con):
    """prata.* minima: as 4 tabelas que o executor exige, com dado util no fato."""
    con.execute("CREATE SCHEMA prata")
    # 3 internacoes: 2 no RJ (uma com obito), 1 em SP
    con.execute("""
        CREATE TABLE prata.internacoes AS SELECT * FROM (VALUES
            ('a1','330455','RJ','Sudeste','A001','p1',1000.00, 4, 40,'Masculino',
             TRUE,  DATE '2026-07-01', DATE '2026-07-05'),
            ('a2','330455','RJ','Sudeste','A001','p1', 500.00, 2, 20,'Feminino',
             FALSE, DATE '2026-07-02', DATE '2026-07-04'),
            ('a3','355030','SP','Sudeste','B002','p2', 300.00, 1, 60,'Masculino',
             FALSE, DATE '2026-07-03', DATE '2026-07-04')
        ) AS t(aih, cod_municipio, uf, regiao, cid_principal, cod_procedimento,
               valor_total, dias_permanencia, idade, sexo, morte,
               data_internacao, data_saida)
    """)
    con.execute(
        "CREATE TABLE prata.cid10 AS "
        "SELECT * FROM (VALUES ('A001','Colera')) AS t(cid, doenca)"
    )
    con.execute(
        "CREATE TABLE prata.municipios AS SELECT * FROM "
        "(VALUES ('330455','Rio','RJ')) AS t(cod_municipio, municipio, uf)"
    )
    con.execute(
        "CREATE TABLE prata.ufs AS SELECT * FROM "
        "(VALUES ('33','RJ','Sudeste')) AS t(cod_uf, uf, regiao)"
    )


def _preparar(tmp_path, monkeypatch):
    banco = tmp_path / "sih.duckdb"
    con = duckdb.connect(str(banco))
    _prata_minima(con)
    con.close()
    pasta = tmp_path / "marts"
    pasta.mkdir()
    monkeypatch.setattr(db, "BANCO", banco)
    monkeypatch.setattr(marts, "PASTA_MARTS", pasta)
    return banco, pasta


def test_arquivo_sem_prefixo_para_antes_de_executar(tmp_path, monkeypatch):
    _, pasta = _preparar(tmp_path, monkeypatch)
    (pasta / "kpis.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    with pytest.raises(SystemExit):
        marts.main()


def test_mart_vazio_encerra(tmp_path, monkeypatch):
    _, pasta = _preparar(tmp_path, monkeypatch)
    (pasta / "00_vazio.sql").write_text(
        "SELECT uf FROM prata.internacoes WHERE uf = 'ZZ'", encoding="utf-8"
    )
    with pytest.raises(SystemExit):
        marts.main()


def test_falta_tabela_prata_encerra(tmp_path, monkeypatch):
    """Se uma tabela esperada da prata nao existir, o executor para antes de rodar."""
    banco, pasta = _preparar(tmp_path, monkeypatch)
    con = duckdb.connect(str(banco))
    con.execute("DROP TABLE prata.cid10")  # derruba uma das 4 exigidas
    con.close()
    (pasta / "00_x.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    with pytest.raises(SystemExit):
        marts.main()


def test_dois_arquivos_mesma_tabela_encerra(tmp_path, monkeypatch):
    """Dois .sql que geram o mesmo nome de tabela ouro param o executor."""
    _, pasta = _preparar(tmp_path, monkeypatch)
    (pasta / "01_kpis.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    (pasta / "02_kpis.sql").write_text("SELECT 2 AS y", encoding="utf-8")
    with pytest.raises(SystemExit):
        marts.main()


def test_sem_nenhum_sql_encerra(tmp_path, monkeypatch):
    """Pasta de marts vazia: nao ha o que executar, encerra."""
    _preparar(tmp_path, monkeypatch)  # pasta criada, mas sem .sql
    with pytest.raises(SystemExit):
        marts.main()


def test_arquivo_apagado_faz_mart_sumir(tmp_path, monkeypatch):
    banco, pasta = _preparar(tmp_path, monkeypatch)
    arq = pasta / "00_teste.sql"
    arq.write_text("SELECT 1 AS x", encoding="utf-8")
    marts.main()
    arq.unlink()
    (pasta / "01_outro.sql").write_text("SELECT 2 AS y", encoding="utf-8")
    marts.main()
    con = duckdb.connect(str(banco))
    sobrou = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'ouro' AND table_name = 'teste'"
    ).fetchone()[0]
    con.close()
    assert sobrou == 0


# --- marts 01 e 02 em SQL, sobre a prata inventada -------------------------
def _ler_sql(nome: str) -> str:
    raiz = Path(__file__).resolve().parent.parent
    return (raiz / "sql" / "marts" / nome).read_text(encoding="utf-8").strip().rstrip(";")


def test_mart01_kpis_bate_com_a_entrada(tmp_path):
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _prata_minima(con)
    r = con.execute(_ler_sql("01_kpis_gerais.sql")).df().iloc[0]
    con.close()
    assert int(r["internacoes"]) == 3
    assert int(r["ufs"]) == 2
    assert float(r["valor_total"]) == 1800.0          # 1000 + 500 + 300
    assert float(r["custo_medio"]) == 600.0           # 1800 / 3
    # 1 obito em 3 internacoes = 33,33%
    assert float(r["taxa_mortalidade_pct"]) == 33.33


def test_mart02_por_estado_agrupa_certo(tmp_path):
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _prata_minima(con)
    r = con.execute(_ler_sql("02_por_estado.sql")).df()
    con.close()
    assert len(r) == 2  # RJ e SP
    rj = r[r["uf"] == "RJ"].iloc[0]
    assert int(rj["internacoes"]) == 2
    assert float(rj["valor_total"]) == 1500.0         # 1000 + 500
    assert float(rj["taxa_mortalidade_pct"]) == 50.0  # 1 obito em 2


def test_mart06_brasil_ranqueia_com_desempate(tmp_path):
    """O mart nacional traz posicao (window) e desempata por cid.

    Na prata minima ha 2 internacoes com cid A001 e 1 com B002, entao A001 fica
    em 1o. A posicao vem de ROW_NUMBER, nao da ordem de leitura."""
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _prata_minima(con)
    r = con.execute(_ler_sql("06_top_diagnosticos_brasil.sql")).df()
    con.close()
    assert list(r["posicao"]) == [1, 2]            # posicao sequencial
    primeiro = r.iloc[0]
    assert primeiro["cid"] == "A001"              # 2 internacoes, lidera
    assert int(primeiro["internacoes"]) == 2
    assert primeiro["doenca"] == "Colera"         # veio do LEFT JOIN cid10
    # participacao pronta: 2 de 3 internacoes = 66,67%
    assert float(primeiro["pct_do_total"]) == 66.67


def test_mart03_por_uf_limita_a_dez_e_ordena(tmp_path):
    """O mart 03 ja entrega o top 10 por UF (posicao <= 10), ordenado."""
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _prata_minima(con)
    r = con.execute(_ler_sql("03_top_diagnosticos.sql")).df()
    con.close()
    # a prata minima tem poucos CIDs, entao nenhuma UF passa de 10 linhas
    assert (r.groupby("uf").size() <= 10).all()
    # dentro de cada UF, posicao comeca em 1 e cresce
    for _uf, grupo in r.groupby("uf"):
        assert list(grupo.sort_values("posicao")["posicao"])[0] == 1
