"""
Baixa os dados brutos do SIH/SUS e grava data/raw/internacoes.parquet.
Roda na SUA maquina (precisa de internet). NAO depende do PySUS.

    uv run python baixar_dados.py

Como funciona:
1. Baixa os arquivos .dbc da AIH reduzida (grupo RD) do FTP do DATASUS, um por
   UF, via HTTPS. Nome do arquivo: RD<UF><AA><MM>.dbc (ex.: RDRJ2604.dbc).
2. Converte cada .dbc para DataFrame com pyreaddbc (biblioteca pequena e
   estavel feita so para o formato do DATASUS).
3. Junta tudo e grava data/raw/internacoes.parquet.

Ajuste ANO, MES e UFS no topo. Por padrao, qualquer UF ausente interrompe a
publicacao do Parquet para impedir totais nacionais incompletos. Para executar
uma amostra parcial conscientemente, use PERMITIR_PARCIAL=1 no ambiente.
"""
import os
import sys
import tempfile
from pathlib import Path

ANO = 2026
MES = 4            # abril
# "todos os estados" = None. Para um teste leve, use por exemplo ["RJ", "SP"].
UFS = None

RAW = Path(__file__).resolve().parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

TODAS_UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
]

# Dois espelhos do mesmo arquivo. O FTP do DATASUS tambem responde por HTTP.
BASES = [
    "https://datasus.saude.gov.br/cgi/dnv/SIHSUS/200801_/Dados/{nome}",
    "ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/{nome}",
]


def _baixar_dbc(nome: str) -> bytes | None:
    """Tenta baixar um .dbc; devolve os bytes ou None se nao achar."""
    import urllib.request

    for base in BASES:
        url = base.format(nome=nome)
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            continue
    return None


def _dbc_para_df(conteudo: bytes, nome: str):
    """Converte bytes de um .dbc em DataFrame.

    O pyreaddbc converte .dbc -> .dbf (funcao dbc2dbf); o .dbf vira DataFrame
    com dbfread. Esse e o caminho estavel entre as versoes do pyreaddbc."""
    import pandas as pd
    import pyreaddbc
    from dbfread import DBF

    caminho_dbc = RAW / nome
    caminho_dbf = RAW / (nome[:-4] + ".dbf")
    caminho_dbc.write_bytes(conteudo)
    try:
        pyreaddbc.dbc2dbf(str(caminho_dbc), str(caminho_dbf))
        registros = DBF(str(caminho_dbf), encoding="latin-1", load=True)
        return pd.DataFrame(iter(registros))
    finally:
        caminho_dbc.unlink(missing_ok=True)
        caminho_dbf.unlink(missing_ok=True)


def _validar_configuracao(ufs):
    """Recusa periodo e siglas invalidos antes de qualquer download."""
    if not isinstance(ANO, int) or not 2000 <= ANO <= 2099:
        raise ValueError("ANO deve estar entre 2000 e 2099")
    if not isinstance(MES, int) or not 1 <= MES <= 12:
        raise ValueError("MES deve estar entre 1 e 12")
    if not ufs or len(set(ufs)) != len(ufs):
        raise ValueError("UFS deve conter siglas unicas e nao pode ser vazia")
    invalidas = sorted(set(ufs) - set(TODAS_UFS))
    if invalidas:
        raise ValueError(f"UF(s) invalidas: {', '.join(invalidas)}")


def main():
    try:
        import pandas as pd  # noqa: F401
        import pyreaddbc  # noqa: F401
        from dbfread import DBF  # noqa: F401
    except Exception as e:  # noqa: BLE001
        print(f"ERRO: falta uma biblioteca ({e}).")
        print("Instale com: uv add pyreaddbc dbfread pandas")
        sys.exit(1)

    ufs = UFS if UFS is not None else TODAS_UFS
    _validar_configuracao(ufs)
    aa = f"{ANO % 100:02d}"
    mm = f"{MES:02d}"

    print(f"Baixando SIH-RD {mm}/{ANO} para {len(ufs)} UF(s)...")
    dfs = []
    faltantes = []
    for uf in ufs:
        nome = f"RD{uf}{aa}{mm}.dbc"
        conteudo = _baixar_dbc(nome)
        if conteudo is None:
            print(f"  - {uf}: nao encontrado")
            faltantes.append(uf)
            continue
        try:
            df = _dbc_para_df(conteudo, nome)
            if df.empty:
                raise ValueError("arquivo convertido sem registros")
            df["UF_ARQUIVO"] = uf
            dfs.append(df)
            print(f"  - {uf}: {len(df):,} linhas".replace(",", "."))
        except Exception as e:  # noqa: BLE001
            print(f"  - {uf}: erro ao converter ({e})")
            faltantes.append(uf)

    if not dfs:
        print("\nNenhum arquivo baixou. Provavel que o mes ainda nao foi")
        print("publicado (o SIH atrasa 2-4 meses). Edite ANO/MES no topo e")
        print("rode de novo com um mes fechado.")
        sys.exit(1)

    if faltantes:
        print(f"\nATENCAO: {len(faltantes)} UF(s) ausentes: {', '.join(faltantes)}")
        if os.environ.get("PERMITIR_PARCIAL") != "1":
            print("ERRO: exportacao bloqueada para evitar dataset incompleto.")
            print("Para uma amostra parcial intencional, defina PERMITIR_PARCIAL=1.")
            sys.exit(1)
        print("AVISO: exportando amostra PARCIAL; nao representa o total nacional.")

    import pandas as pd
    todos = pd.concat(dfs, ignore_index=True)
    destino = RAW / "internacoes.parquet"
    # Publicacao atomica: falha de escrita nao corrompe o Parquet anterior.
    RAW.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".internacoes-", suffix=".parquet", dir=RAW, delete=False
        ) as arquivo:
            temporario = Path(arquivo.name)
        todos.to_parquet(temporario, index=False)
        temporario.replace(destino)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)
    print(f"\n  ok: {destino} ({len(todos):,} linhas)".replace(",", "."))
    print("\nAgora gere os dicionarios:")
    print("  uv run python gerar_dicionarios.py")


if __name__ == "__main__":
    main()
