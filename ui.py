"""
Abre a interface web local do DuckDB (DuckDB UI) sobre o sih.duckdb.

Permite explorar os schemas bronze, prata e ouro pelo navegador em
http://localhost:4213 sem precisar abrir sessao interativa no terminal.
Se o banco ainda nao existir, avisa e encerra sem criar arquivo vazio.

    uv run python ui.py
"""
import sys
import time

import duckdb

from pipeline.db import BANCO

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    if not BANCO.exists():
        print(f"ERRO: banco {BANCO.name} nao encontrado na raiz do projeto.")
        print("Rode antes: uv run python -m pipeline.ingestao")
        sys.exit(1)

    con = duckdb.connect(str(BANCO))
    try:
        con.execute("INSTALL ui; LOAD ui; CALL start_ui();")
        print(f"DuckDB UI aberta sobre {BANCO.name} em http://localhost:4213")
        print("Pressione Ctrl+C para encerrar.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando DuckDB UI.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
