"""
Etapa 4: qualidade de dados (checagens sobre o banco ja gravado).

Roda depois do pipeline e falha (sys.exit 1) se qualquer regra nao fechar. A
ideia e a da aula: o erro em dados nao estoura sozinho, aparece como numero
errado; entao a conferencia que a gente faria na mao vira codigo que trava o
build. Cada regra e um SELECT que devolve TRUE quando esta tudo certo.

As familias de regra cobertas (Aula 4):
  1. Nao vazio          todo mart tem pelo menos 1 linha.
  2. Chave unica        o grao declarado e real (count = count distinct).
  3. Dentro do dominio   percentual 0..100, idade >= 0, sexo/uf conhecidos.
  4. Partes somam o todo perfil e por_estado somam o total dos KPIs.
  5. Dois caminhos        o total sai igual por marts diferentes.
  6. Nada some sem aviso  prata vem de bronze sem perda silenciosa.

Rodar com:
    uv run python -m pipeline.qualidade
"""
import sys

from pipeline.db import conectar

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Tabelas da camada ouro que nunca podem voltar vazias.
MARTS = [
    "kpis_gerais", "por_estado", "top_diagnosticos", "perfil_demografico",
    "internacoes_diarias", "top_diagnosticos_brasil",
    "internacoes_diarias_brasil", "perfil_demografico_brasil",
    "mortalidade_por_cid", "municipios_pareto",
]


def _regras(con) -> list[tuple[str, str]]:
    """Lista de (descricao, SQL que devolve TRUE quando a regra passa)."""
    regras: list[tuple[str, str]] = []

    # 1. Nao vazio: cada mart tem ao menos 1 linha.
    for m in MARTS:
        regras.append((
            f"Nao vazio: ouro.{m} tem linhas",
            f"SELECT count(*) > 0 FROM ouro.{m}",
        ))

    regras += [
        # 2. Chave unica / grao: 1 linha por AIH na prata.
        ("Grao: prata.internacoes e 1 linha por AIH (count = count distinct)",
         "SELECT count(*) = count(DISTINCT aih) FROM prata.internacoes"),

        # 2. Chave unica: por_estado tem 1 linha por UF.
        ("Chave unica: ouro.por_estado tem 1 linha por UF",
         "SELECT count(*) = count(DISTINCT uf) FROM ouro.por_estado"),

        # 3. Dominio: taxa de mortalidade entre 0 e 100 em todas as UFs.
        ("Dominio: taxa_mortalidade_pct entre 0 e 100 em por_estado",
         "SELECT bool_and(taxa_mortalidade_pct BETWEEN 0 AND 100) FROM ouro.por_estado"),

        # Integridade financeira: pagamentos e permanencia nao podem ser negativos.
        ("Dominio: valor_total da prata e nao negativo e nao nulo",
         """SELECT count(*) FILTER (
                WHERE valor_total IS NULL OR valor_total < 0
            ) = 0 FROM prata.internacoes"""),

        ("Dominio: dias_permanencia da prata e nao negativo",
         """SELECT count(*) FILTER (
                WHERE dias_permanencia < 0
            ) = 0 FROM prata.internacoes"""),

        # 3. Dominio: nenhuma idade negativa na prata (COD_IDADE bem aplicado).
        ("Dominio: nenhuma idade negativa em prata.internacoes",
         "SELECT count(*) FILTER (WHERE idade < 0) = 0 FROM prata.internacoes"),

        # 3. Dominio: UF sempre entre as 27 siglas conhecidas (quando nao nula).
        ("Dominio: toda UF preenchida esta entre as 27 siglas validas",
         """SELECT count(*) FILTER (
                WHERE uf IS NOT NULL AND uf NOT IN (
                  'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS',
                  'MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC',
                  'SP','SE','TO')
            ) = 0 FROM prata.internacoes"""),

        # 4. Partes somam o todo: perfil nacional soma o total dos KPIs.
        ("Partes somam o todo: soma do perfil_demografico_brasil = total de internacoes",
         """SELECT (SELECT sum(internacoes) FROM ouro.perfil_demografico_brasil)
                 = (SELECT internacoes FROM ouro.kpis_gerais)"""),

        # 4. Partes somam o todo: top_diagnosticos_brasil soma o total.
        ("Partes somam o todo: soma do top_diagnosticos_brasil = total de internacoes",
         """SELECT (SELECT sum(internacoes) FROM ouro.top_diagnosticos_brasil)
                 = (SELECT internacoes FROM ouro.kpis_gerais)"""),

        # 5. Dois caminhos concordam: o total por por_estado = KPI, e o gasto tambem.
        ("Dois caminhos concordam: por_estado soma o mesmo total e gasto dos KPIs",
         """SELECT (SELECT sum(internacoes) FROM ouro.por_estado)
                 = (SELECT internacoes FROM ouro.kpis_gerais)
              AND round((SELECT sum(valor_total) FROM ouro.por_estado), 2)
                 = round((SELECT valor_total FROM ouro.kpis_gerais), 2)"""),

        # 6. Nada some sem aviso: a prata nunca tem mais linhas que a bronze
        #    (so pode ter removido linhas sem valor, nunca inventado).
        ("Nada some sem aviso: prata.internacoes <= bronze.internacoes",
         """SELECT (SELECT count(*) FROM prata.internacoes)
                <= (SELECT count(*) FROM bronze.internacoes)"""),

        # Reconciliacao por AIH e valor, depois das exclusoes previstas.
        ("Reconciliacao: AIHs e valores da prata correspondem a bronze elegivel",
         """WITH classificadas AS (
                SELECT CAST(N_AIH AS VARCHAR) AS aih,
                       NULLIF(TRIM(CAST(VAL_TOT AS VARCHAR)), '') AS valor,
                       row_number() OVER (
                           PARTITION BY CAST(N_AIH AS VARCHAR)
                           ORDER BY DT_SAIDA DESC NULLS LAST,
                                    CAST(NULLIF(TRIM(CAST(VAL_TOT AS VARCHAR)), '')
                                         AS DECIMAL(12,2)) DESC NULLS LAST
                       ) AS posicao
                FROM bronze.internacoes
            ), esperadas AS (
                SELECT aih, CAST(valor AS DECIMAL(12,2)) AS valor_total
                FROM classificadas WHERE posicao = 1 AND valor IS NOT NULL
            ), faltantes AS (
                SELECT * FROM esperadas
                EXCEPT ALL SELECT aih, valor_total FROM prata.internacoes
            ), inesperadas AS (
                SELECT aih, valor_total FROM prata.internacoes
                EXCEPT ALL SELECT * FROM esperadas
            )
            SELECT NOT EXISTS (SELECT 1 FROM faltantes)
               AND NOT EXISTS (SELECT 1 FROM inesperadas)"""),

        ("Reconciliacao: KPI confere com quantidade e valor total da prata",
         """SELECT (SELECT count(*) FROM ouro.kpis_gerais) = 1
               AND (SELECT internacoes FROM ouro.kpis_gerais)
                   = (SELECT count(*) FROM prata.internacoes)
               AND (SELECT valor_total FROM ouro.kpis_gerais)
                   = (SELECT sum(valor_total) FROM prata.internacoes)"""),

        # 2b. Chave unica nos dicionarios: um codigo nao pode ter duas linhas,
        #     senao o LEFT JOIN da camada ouro multiplicaria internacoes.
        ("Chave unica: prata.cid10 tem 1 linha por codigo CID",
         "SELECT count(*) = count(DISTINCT cid) FROM prata.cid10"),
        ("Chave unica: prata.municipios tem 1 linha por codigo de municipio",
         "SELECT count(*) = count(DISTINCT cod_municipio) FROM prata.municipios"),

        # 3b. Nomes reais, nao modo neutro: se o dicionario de CID caiu no
        #     fallback sem internet, as descricoes viram 'CID <codigo>'. A regra
        #     falha se MAIS da metade das doencas do top nacional estiver nesse
        #     formato, sinal de que os nomes reais nao foram baixados.
        ("Nomes reais: top_diagnosticos_brasil nao esta em modo neutro (CID <codigo>)",
         """SELECT count(*) FILTER (WHERE doenca = 'CID ' || cid) < count(*) / 2
            FROM ouro.top_diagnosticos_brasil"""),

        # 5b. Dois caminhos concordam, por-UF x nacional: a soma das internacoes
        #     do perfil por UF bate com o total do perfil nacional.
        ("Dois caminhos concordam: soma do perfil por UF = perfil nacional",
         """SELECT (SELECT sum(internacoes) FROM ouro.perfil_demografico)
                 = (SELECT sum(internacoes) FROM ouro.perfil_demografico_brasil)"""),

        # 5c. Dois caminhos concordam: a serie diaria por UF soma o mesmo que a
        #     serie nacional (ambas no mesmo recorte de data de entrada).
        ("Dois caminhos concordam: soma da serie diaria por UF = serie nacional",
         """SELECT (SELECT sum(internacoes) FROM ouro.internacoes_diarias)
                 = (SELECT sum(internacoes) FROM ouro.internacoes_diarias_brasil)"""),

        # 4b. Partes somam o todo no mart de mortalidade: obitos <= internacoes
        #     em todo CID, e a taxa fica no dominio 0..100.
        ("Dominio: mortalidade_por_cid tem obitos <= internacoes e taxa 0..100",
         """SELECT bool_and(obitos <= internacoes
                            AND taxa_mortalidade_pct BETWEEN 0 AND 100)
            FROM ouro.mortalidade_por_cid"""),

        # Integridade dos marts complementares: grão, elegibilidade e acumulado.
        ("Chave unica: mortalidade_por_cid tem 1 linha por CID",
         "SELECT count(*) = count(DISTINCT cid) FROM ouro.mortalidade_por_cid"),

        ("Elegibilidade: mortalidade_por_cid inclui apenas CID com 100+ AIHs",
         "SELECT count(*) FILTER (WHERE internacoes < 100) = 0 FROM ouro.mortalidade_por_cid"),

        ("Chave unica: municipios_pareto tem 1 linha por municipio",
         """SELECT count(*) = count(DISTINCT cod_municipio)
            FROM ouro.municipios_pareto"""),

        ("Pareto: posicoes sequenciais, percentuais validos e acumulado crescente",
         """WITH sequencia AS (
                SELECT posicao, pct_acumulado,
                       lag(pct_acumulado) OVER (ORDER BY posicao) AS anterior
                FROM ouro.municipios_pareto
            )
            SELECT count(*) = count(DISTINCT posicao)
               AND min(posicao) = 1
               AND max(posicao) = count(*)
               AND count(*) FILTER (
                   WHERE pct_acumulado IS NULL
                      OR pct_acumulado NOT BETWEEN 0 AND 100
                      OR (anterior IS NOT NULL AND pct_acumulado < anterior)
               ) = 0
            FROM sequencia"""),

        # 5d. Pareto fecha em 100%: a ultima linha do acumulado chega a 100.
        ("Pareto: municipios_pareto termina em 100% acumulado",
         """SELECT round(max(pct_acumulado)) = 100 FROM ouro.municipios_pareto"""),
    ]
    return regras


def main():
    """Roda todas as regras de qualidade; encerra com erro se alguma falhar."""
    con = conectar()
    regras = _regras(con)

    falhas = 0
    try:
        for descricao, sql in regras:
            ok = bool(con.execute(sql).fetchone()[0])
            print(f"  {'OK ' if ok else 'FALHOU'} {descricao}")
            if not ok:
                falhas += 1
    finally:
        con.close()

    if falhas:
        print(f"\nERRO: {falhas} regra(s) de qualidade falharam.", file=sys.stderr)
        sys.exit(1)
    print(f"\n  {len(regras)} regras de qualidade verificadas, todas passaram.")


if __name__ == "__main__":
    main()
