"""
Testes de pipeline/transformacao.py: a decodificacao dos codigos do SIH.

Monta um schema bronze minimo com dado inventado (poucas AIH, cada uma testando
uma regra) e roda a transformacao. O valor esperado sai da entrada.
"""
import duckdb

from pipeline import db, transformacao


def _bronze_minimo(con):
    con.execute("CREATE SCHEMA bronze")
    # 5 internacoes (a coluna COD_IDADE e a unidade da idade no SIH):
    #   a1: RJ, homem, obito, R$ 1.500,50, 5 dias, 40 anos (COD_IDADE 4)
    #   a2: SP, mulher, sem obito, R$ 800,00, 2 dias, 30 anos (COD_IDADE 4)
    #   a3: valor nulo -> deve ser descartada (WHERE valor_total IS NOT NULL)
    #   a4: bebe de 5 MESES (IDADE 5, COD_IDADE 3) -> idade em anos tem que ser 0
    #   a5: centenario (IDADE 2, COD_IDADE 5) -> idade em anos tem que ser 102
    con.execute("""
        CREATE TABLE bronze.internacoes AS SELECT * FROM (VALUES
            ('a1','330455','A001','0303010011','1500.50','5','40','4','1','1','20260701','20260706'),
            ('a2','355030','B002','0303010022', '800.00','2','30','4','3','0','20260702','20260704'),
            ('a3','330455','A001','0303010011',     NULL,'1','50','4','1','0','20260703','20260704'),
            ('a4','330455','P001','0303010033', '400.00','3', '5','3','1','0','20260704','20260707'),
            ('a5','355030','I001','0303010044', '900.00','4', '2','5','3','0','20260705','20260709')
        ) AS t(N_AIH, MUNIC_RES, DIAG_PRINC, PROC_REA, VAL_TOT, DIAS_PERM,
               IDADE, COD_IDADE, SEXO, MORTE, DT_INTER, DT_SAIDA)
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
    assert n == 4  # entraram 5, so a de valor nulo (a3) saiu


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


def test_grao_uma_linha_por_aih(tmp_path, monkeypatch):
    """O grao da prata e 1 linha por AIH: count(*) == count(DISTINCT aih)."""
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    total, distintas = con.execute(
        "SELECT count(*), count(DISTINCT aih) FROM prata.internacoes"
    ).fetchone()
    con.close()
    assert total == distintas


def test_idade_em_anos_respeita_cod_idade(tmp_path, monkeypatch):
    """COD_IDADE e a unidade: bebe em meses vira 0 ano, centenario soma 100.

    a4 = IDADE 5, COD_IDADE 3 (meses) -> 0 anos (menos de 1 ano).
    a5 = IDADE 2, COD_IDADE 5 (anos 100+) -> 102 anos.
    a1 = IDADE 40, COD_IDADE 4 (anos) -> 40 anos (caso comum, inalterado)."""
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    idades = dict(con.execute(
        "SELECT aih, idade FROM prata.internacoes"
    ).fetchall())
    con.close()
    assert idades["a4"] == 0     # 5 meses -> 0 ano
    assert idades["a5"] == 102   # 2 + 100 (centenario)
    assert idades["a1"] == 40    # anos, sem mexer


def test_dicionarios_tipados_e_renomeados(tmp_path, monkeypatch):
    """cid10 e municipios viram tabelas de apoio com as colunas renomeadas."""
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    cid_cols = [r[0] for r in con.execute("DESCRIBE prata.cid10").fetchall()]
    mun_cols = [r[0] for r in con.execute("DESCRIBE prata.municipios").fetchall()]
    n_cid = con.execute("SELECT count(*) FROM prata.cid10").fetchone()[0]
    con.close()
    assert cid_cols == ["cid", "doenca"]
    assert mun_cols == ["cod_municipio", "municipio", "uf"]
    assert n_cid == 2
