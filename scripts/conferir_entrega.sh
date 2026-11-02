#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
ORIGEM_DADOS="${1:-}"
uv sync --frozen
uv run ruff check .
uv run pytest --cov
uv run python - "$ORIGEM_DADOS" <<'PY'
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb
import gerar_dicionarios

raiz = Path.cwd().resolve()
relatorio = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
manifesto = json.loads((raiz / "docs/proveniencia-extracao.json").read_text())
for nome, esperado in manifesto["csvs_sha256"].items():
    caminho = raiz / "dados_painel" / nome
    assert hashlib.sha256(caminho.read_bytes()).hexdigest() == esperado, f"Hash divergente: {nome}"
print("OK: hashes dos dez CSVs publicados")

if not sys.argv[1]:
    raise SystemExit("Informe a pasta original do projeto para conferir os arquivos brutos.")
origem = Path(sys.argv[1]).expanduser().resolve()
assert origem != raiz, "Execute em uma cópia isolada, diferente da pasta original."
parquet = origem / "data/raw/internacoes.parquet"
municipios = origem / "data/raw/municipios.csv"
assert parquet.is_file() and municipios.is_file(), "Faltam arquivos na pasta original."
assert hashlib.sha256(parquet.read_bytes()).hexdigest() == manifesto["arquivos_entrada_sha256"]["internacoes.parquet"], "O Parquet é diferente do registrado no manifesto."
destino = raiz / "data/raw"
destino.mkdir(parents=True, exist_ok=True)
for nome in ["internacoes.parquet", "municipios.csv", "cid10.csv"]:
    arquivo = destino / nome
    assert not arquivo.exists() and not arquivo.is_symlink(), "Use uma cópia isolada nova."
(destino / "internacoes.parquet").symlink_to(parquet)
shutil.copyfile(municipios, destino / "municipios.csv")
con = duckdb.connect()
codigos = {r[0] for r in con.execute("SELECT DISTINCT CAST(DIAG_PRINC AS VARCHAR) FROM read_parquet(?)", [str(parquet)]).fetchall()}
con.close()
gerar_dicionarios.gerar_cid(codigos)
subprocess.run([sys.executable, "executar.py"], check=True)

con = duckdb.connect(str(raiz / "sih.duckdb"), read_only=True)
kpi = con.execute("SELECT * FROM ouro.kpis_gerais").df().iloc[0]
valor = con.execute("SELECT CAST(valor_total AS VARCHAR) FROM ouro.kpis_gerais").fetchone()[0]
print("\nValor total com centavos:", valor)
print("\nKPIs:", kpi.to_dict())
assert con.execute("SELECT count(*) FROM prata.internacoes").fetchone()[0] == 1238234
assert Decimal(valor) == Decimal("2258865118.36"), "O valor financeiro divergiu dos CSVs publicados."

comparacoes = {}
for nome in manifesto["csvs_sha256"]:
    mart = Path(nome).stem
    campos = con.execute(f"DESCRIBE ouro.{mart}").fetchall()
    colunas = [r[0] for r in campos]
    with (raiz / "dados_painel" / nome).open(newline="") as arquivo:
        publicado = list(csv.DictReader(arquivo))
    assert set(publicado[0]) == set(colunas), f"Colunas divergentes: {mart}"
    def normalizar(linha):
        valores = []
        for posicao, (coluna, tipo, *_) in enumerate(campos):
            valor_campo = linha[coluna] if isinstance(linha, dict) else linha[posicao]
            if valor_campo is None or valor_campo == "":
                valores.append(None)
            elif any(t in tipo for t in ["INT", "DECIMAL", "FLOAT", "DOUBLE", "REAL"]):
                valores.append(Decimal(str(valor_campo)).quantize(Decimal("0.000001")))
            elif isinstance(valor_campo, (date, datetime)):
                valores.append(valor_campo.isoformat())
            else:
                valores.append(str(valor_campo))
        return tuple(valores)
    anterior = Counter(normalizar(r) for r in publicado)
    atual = Counter(normalizar(r) for r in con.execute(f"SELECT * FROM ouro.{mart}").fetchall())
    comparacoes[mart] = {"igual": anterior == atual, "somente_publicado": sum((anterior-atual).values()), "somente_local": sum((atual-anterior).values())}
    print("OK" if anterior == atual else "DIFERENTE", mart, comparacoes[mart])

print("\nUnidades de idade na origem:")
print(con.execute("SELECT COD_IDADE, count(*) AS registros FROM bronze.internacoes GROUP BY 1 ORDER BY 1").df().to_string(index=False))
print("\nDatas registradas antes de fevereiro de 2008:")
print(con.execute("SELECT data_internacao, count(*) AS registros FROM prata.internacoes WHERE data_internacao < DATE '2008-02-01' GROUP BY 1 ORDER BY 2 DESC LIMIT 5").df().to_string(index=False))
print("\nCompetências:")
print(con.execute("SELECT ANO_CMPT, MES_CMPT, count(*) AS registros FROM bronze.internacoes GROUP BY 1,2 ORDER BY 1,2").df().to_string(index=False))
relatorio["comparacao_marts"] = comparacoes
relatorio["valor_total"] = valor
relatorio["internacoes"] = 1238234
con.close()
subprocess.run([sys.executable, "relatorio.py"], check=True)
html = (raiz / "docs/relatorio.html").read_text()
assert all(f'id="g{i:02d}"' in html for i in range(9)), "Faltam figuras no HTML."
assert 'class="mapa-relatorio"' in html
falhas = [nome for nome, dados in comparacoes.items() if not dados["igual"]]
relatorio["aprovado"] = not falhas
(raiz / "conferencia-final.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n")
if falhas:
    raise SystemExit("Conferência requer revisão. Marts diferentes: " + ", ".join(falhas))
print("\nCONFERÊNCIA APROVADA: dez marts iguais, valores exatos e nove figuras no HTML.")
print("Os arquivos originais não foram modificados. Resultado: conferencia-final.json")
PY
