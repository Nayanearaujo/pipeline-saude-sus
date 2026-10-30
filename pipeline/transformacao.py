"""
Etapa 2: transformacao (bronze -> prata).

Pega a tabela-fato de internacoes (SIH-RD) e os dois dicionarios, da a cada
coluna o tipo do que ela realmente e, decodifica os codigos cripticos do SIH
(sexo, UF, morte) e renomeia tudo para portugues legivel. Uma linha = uma
internacao (AIH): a dedup e por aih (QUALIFY), nao DISTINCT da linha inteira.
Mantem os dicionarios como tabelas de apoio para o JOIN da camada ouro.

Decisoes de dado (resumo; cada uma com o motivo no codigo):
- Valor (VAL_TOT) vira DECIMAL(12,2): e dinheiro, nunca DOUBLE.
- Datas (DT_INTER, DT_SAIDA) viram DATE a partir do formato AAAAMMDD do SIH.
- Dias de permanencia viram INTEGER.
- Idade: idade_anos combina IDADE com COD_IDADE (a unidade do SIH). COD_IDADE
  0/1/2/3 (minutos/horas/dias/meses) -> menos de 1 ano, entra como 0; 4 ->
  IDADE em anos; 5 -> IDADE + 100 (centenarios). Sem isso, um bebe de 5 meses
  (IDADE=5, COD_IDADE=3) seria lido como 5 anos.
- Codigo do municipio e o prefixo de 6 digitos do IBGE; fica VARCHAR (e id).
- Sexo: '1'->Masculino, '3'->Feminino (codificacao do SIH); outros -> NULL.
- MORTE: '1' indica obito na internacao; vira BOOLEAN morte.
- UF sai do codigo IBGE do municipio (2 primeiros digitos) via tabela de UFs.

Reexecucao: CREATE OR REPLACE TABLE, nunca append. Rodar com:
    uv run python -m pipeline.transformacao
"""
import sys

from pipeline.db import conectar, criar_schema

sys.stdout.reconfigure(encoding="utf-8")

# Codigo IBGE da UF (2 digitos) -> sigla e regiao. Tabela pequena e estavel.
UFS = {
    "11": ("RO", "Norte"), "12": ("AC", "Norte"), "13": ("AM", "Norte"),
    "14": ("RR", "Norte"), "15": ("PA", "Norte"), "16": ("AP", "Norte"),
    "17": ("TO", "Norte"), "21": ("MA", "Nordeste"), "22": ("PI", "Nordeste"),
    "23": ("CE", "Nordeste"), "24": ("RN", "Nordeste"), "25": ("PB", "Nordeste"),
    "26": ("PE", "Nordeste"), "27": ("AL", "Nordeste"), "28": ("SE", "Nordeste"),
    "29": ("BA", "Nordeste"), "31": ("MG", "Sudeste"), "32": ("ES", "Sudeste"),
    "33": ("RJ", "Sudeste"), "35": ("SP", "Sudeste"), "41": ("PR", "Sul"),
    "42": ("SC", "Sul"), "43": ("RS", "Sul"), "50": ("MS", "Centro-Oeste"),
    "51": ("MT", "Centro-Oeste"), "52": ("GO", "Centro-Oeste"),
    "53": ("DF", "Centro-Oeste"),
}


def _tabela_ufs(con):
    """Materializa o dicionario de UFs como tabela auxiliar em prata."""
    con.execute("DROP TABLE IF EXISTS prata.ufs")
    con.execute("CREATE TABLE prata.ufs (cod_uf VARCHAR, uf VARCHAR, regiao VARCHAR)")
    con.executemany(
        "INSERT INTO prata.ufs VALUES (?, ?, ?)",
        [(cod, sigla, regiao) for cod, (sigla, regiao) in UFS.items()],
    )


# A transformacao da tabela-fato. Os nomes a esquerda sao os do SIH-RD; os da
# direita sao o vocabulario legivel que vou usar nos JOINs da camada ouro.
SQL_INTERNACOES = """
CREATE OR REPLACE TABLE prata.internacoes AS
WITH base AS (
    -- Grao: 1 linha = 1 AIH. Dedup explicita por aih (QUALIFY), nao DISTINCT da
    -- linha inteira: duas AIH distintas com todos os campos iguais nao podem
    -- colapsar numa so. Fica a primeira ocorrencia de cada aih.
    SELECT
        CAST(N_AIH AS VARCHAR)                             AS aih,
        substr(CAST(MUNIC_RES AS VARCHAR), 1, 6)           AS cod_municipio,
        substr(CAST(MUNIC_RES AS VARCHAR), 1, 2)           AS cod_uf,
        CAST(DIAG_PRINC AS VARCHAR)                        AS cid_principal,
        CAST(PROC_REA AS VARCHAR)                          AS cod_procedimento,
        TRY_CAST(VAL_TOT AS DECIMAL(12,2))                 AS valor_total,
        TRY_CAST(DIAS_PERM AS INTEGER)                     AS dias_permanencia,
        -- idade em ANOS, combinando IDADE com COD_IDADE (a unidade no SIH):
        -- 0/1/2/3 = minutos/horas/dias/meses -> < 1 ano (0); 4 = anos; 5 = 100+.
        CASE CAST(COD_IDADE AS VARCHAR)
            WHEN '5' THEN TRY_CAST(IDADE AS INTEGER) + 100
            WHEN '4' THEN TRY_CAST(IDADE AS INTEGER)
            WHEN '0' THEN 0
            WHEN '1' THEN 0
            WHEN '2' THEN 0
            WHEN '3' THEN 0
            ELSE TRY_CAST(IDADE AS INTEGER)
        END                                                AS idade,
        CASE CAST(SEXO AS VARCHAR)
            WHEN '1' THEN 'Masculino'
            WHEN '3' THEN 'Feminino'
            ELSE NULL END                                  AS sexo,
        (CAST(MORTE AS VARCHAR) = '1')                     AS morte,
        TRY_CAST(strptime(CAST(DT_INTER AS VARCHAR), '%Y%m%d') AS DATE) AS data_internacao,
        TRY_CAST(strptime(CAST(DT_SAIDA AS VARCHAR), '%Y%m%d') AS DATE) AS data_saida
    FROM bronze.internacoes
    QUALIFY row_number() OVER (PARTITION BY CAST(N_AIH AS VARCHAR) ORDER BY 1) = 1
)
SELECT
    b.aih,
    b.cod_municipio,
    u.uf,
    u.regiao,
    b.cid_principal,
    b.cod_procedimento,
    b.valor_total,
    b.dias_permanencia,
    b.idade,
    b.sexo,
    b.morte,
    b.data_internacao,
    b.data_saida
FROM base b
LEFT JOIN prata.ufs u ON u.cod_uf = b.cod_uf
WHERE b.valor_total IS NOT NULL
"""

# Dicionarios: tipados e renomeados, sem agregar.
SQL_CID = """
CREATE OR REPLACE TABLE prata.cid10 AS
SELECT DISTINCT
    CAST(codigo AS VARCHAR)   AS cid,
    CAST(descricao AS VARCHAR) AS doenca
FROM bronze.cid10
"""

SQL_MUNICIPIOS = """
CREATE OR REPLACE TABLE prata.municipios AS
SELECT DISTINCT
    substr(CAST(codigo AS VARCHAR), 1, 6) AS cod_municipio,
    CAST(municipio AS VARCHAR)            AS municipio,
    CAST(uf AS VARCHAR)                   AS uf
FROM bronze.municipios
"""


def main():
    """Transforma a bronze na prata: tipa, decodifica os códigos do SIH e renomeia."""
    con = conectar()
    criar_schema(con, "prata")

    _tabela_ufs(con)

    etapas = [
        ("internacoes", SQL_INTERNACOES),
        ("cid10", SQL_CID),
        ("municipios", SQL_MUNICIPIOS),
    ]

    total = 0
    for nome, sql in etapas:
        origem = con.execute(
            f"SELECT count(*) FROM bronze.{nome}"
        ).fetchone()[0]
        con.execute(sql)
        destino = con.execute(f"SELECT count(*) FROM prata.{nome}").fetchone()[0]
        total += destino
        saiu = origem - destino
        marca = f"(-{saiu:,} removidas)".replace(",", ".") if saiu else "(0 removidas)"
        print(f"  prata.{nome:<14} {destino:>9,} linhas  {marca}".replace(",", "."))

    print(f"  {'total':<14} {total:>9,} linhas".replace(",", "."))
    con.close()


if __name__ == "__main__":
    main()
