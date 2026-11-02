"""Auditoria conserva dados e separa alertas de diagnósticos de causa."""
import duckdb
from test_marts import _prata_minima

from pipeline import auditoria, db


def test_achados_sao_agregados_sem_alterar_registros(tmp_path, monkeypatch):
    banco = tmp_path / 'auditoria.duckdb'
    with duckdb.connect(str(banco)) as con:
        _prata_minima(con)
        con.execute("UPDATE prata.internacoes SET data_internacao = DATE '2008-01-01' WHERE aih='a1'")
        con.execute("UPDATE prata.internacoes SET data_saida = DATE '2026-06-01' WHERE aih='a2'")
        antes = con.execute('SELECT * FROM prata.internacoes ORDER BY aih').fetchall()
        t = auditoria.tabelas(con)
        assert t['cid_sem_descricao'].iloc[0]['cid'] == 'B002'
        assert t['cid_sem_descricao'].iloc[0]['internacoes'] == 1
        assert t['datas_para_investigar'].entrada_antiga.sum() == 1
        assert t['datas_para_investigar'].saida_anterior_entrada.sum() == 1
        assert t['entradas_por_mes'].internacoes.sum() == 3
        assert all('aih' not in x.columns for x in t.values())
        assert con.execute('SELECT * FROM prata.internacoes ORDER BY aih').fetchall() == antes
    monkeypatch.setattr(db, 'BANCO', banco)
    monkeypatch.setattr(auditoria, 'DESTINO', tmp_path / 'resultado')
    auditoria.main()
    assert len(list((tmp_path / 'resultado').glob('*.csv'))) == 3


def test_sem_alertas_gera_tabelas_vazias_com_cabecalho():
    with duckdb.connect() as con:
        _prata_minima(con)
        con.execute("INSERT INTO prata.cid10 VALUES ('B002','Descrição conhecida')")
        t = auditoria.tabelas(con)
        assert t['cid_sem_descricao'].empty
        assert t['datas_para_investigar'].empty
