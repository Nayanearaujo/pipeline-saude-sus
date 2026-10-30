"""
Testes de pipeline/transformacao.py: a decodificacao dos codigos do SIH.

Monta um schema bronze minimo com dado inventado (poucas AIH, cada uma testando
uma regra) e roda a transformacao. O valor esperado sai da entrada.
"""
import duckdb

from pipeline import db, transformacao


def _bronze_minimo(con):
    con.execute("CREATE SCHEMA bronze")
    # 3 internacoes:
    #   a1: RJ (munic 330455), homem, obito, R$ 1.500,50, 5 dias, 40 anos
    #   a2: SP (munic 355030), mulher, sem obito, R$ 800,00, 2 dias, 30 anos
    #   a3: valor nulo -> deve ser descartada (WHERE valor_total IS NOT NULL)
    con.execute("""
        CREATE TABLE bronze.internacoes AS SELECT * FROM (VALUES
            ('a1','330455','A001','0303010011','1500.50','5','40','1','1','20260701','20260706'),
            ('a2','355030','B002','0303010022', '800.00','2','30','3','0','20260702','20260704'),
            ('a3','330455','A001','0303010011',     NULL,'1','50','1','0','20260703','20260704')
        ) AS t(N_AIH, MUNIC_RES, DIAG_PRINC, PROC_REA, VAL_TOT, DIAS_PERM,
               IDADE, SEXO, MORTE, DT_INTER, DT_SAIDA)
    """)
    con.execute("""
        CREATE TABLE bronze.cid10 AS SELECT * FROM (VALUES
            ('A001','Colera'), ('B002','Dengue')
        ) AS t(codigo, descricao)
    """)
    con.execute("""
        CREATE TABLE bronze.municipios AS SELECT * FROM (VALUES
            ('330455','Rio de Janeiro','RJ'), ('355030','Sao Paulo','SP')
        ) AS t(codigo, municipio, uf)
    """)


def _preparar(tmp_path, monkeypatch):
    banco = tmp_path / "sih.duckdb"
    con = duckdb.connect(str(banco))
    _bronze_minimo(con)
    con.close()
    monkeypatch.setattr(db, "BANCO", banco)
    return banco


def test_valor_nulo_e_descartado(tmp_path, monkeypatch):
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    n = con.execute("SELECT count(*) FROM prata.internacoes").fetchone()[0]
    con.close()
    assert n == 2  # entraram 3, a de valor nulo saiu


def test_decodifica_sexo_uf_morte_e_tipos(tmp_path, monkeypatch):
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    linha = con.execute("""
        SELECT uf, regiao, sexo, morte, valor_total, dias_permanencia, data_internacao
        FROM prata.internacoes WHERE aih = 'a1'
    """).fetchone()
    tipos = dict((r[0], r[1]) for r in con.execute("DESCRIBE prata.internacoes").fetchall())
    con.close()
    uf, regiao, sexo, morte, valor, dias, dt = linha
    assert uf == "RJ"
    assert regiao == "Sudeste"
    assert sexo == "Masculino"      # codigo '1'
    assert morte is True            # codigo '1'
    assert float(valor) == 1500.50
    assert dias == 5
    assert str(dt) == "2026-07-01"  # AAAAMMDD -> DATE
    assert tipos["valor_total"].startswith("DECIMAL")


def test_sexo_feminino_e_sem_obito(tmp_path, monkeypatch):
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    sexo, morte = con.execute(
        "SELECT sexo, morte FROM prata.internacoes WHERE aih = 'a2'"
    ).fetchone()
    con.close()
    assert sexo == "Feminino"   # codigo '3'
    assert morte is False       # codigo '0'
