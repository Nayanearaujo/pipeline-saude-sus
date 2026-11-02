"""Orquestração sem acessar banco ou rede."""
import pytest

import executar


def test_etapas_em_ordem_e_interrupcao(monkeypatch):
    chamadas = []
    monkeypatch.setattr(executar, 'ETAPAS', [('ingestao', lambda: chamadas.append(1)),
                                          ('qualidade', lambda: chamadas.append(2))])
    executar.main()
    assert chamadas == [1, 2]
    def falha():
        raise SystemExit(1)
    monkeypatch.setattr(executar, 'ETAPAS', [('falha', falha), ('proibida', lambda: chamadas.append(3))])
    with pytest.raises(SystemExit):
        executar.main()
    assert chamadas == [1, 2]
