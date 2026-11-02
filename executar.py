"""
Executa o pipeline inteiro numa tacada: bronze -> prata -> ouro -> qualidade.

Atalho para o corretor e para o dia a dia. Pressupoe que os dados já estão em
data/raw/ (rode antes baixar_dados.py e gerar_dicionarios.py). Para o painel,
rode depois: uv run streamlit run app.py

    uv run python executar.py
"""
import sys

from pipeline import auditoria, ingestao, marts, qualidade, transformacao

ETAPAS = [
    ("1/5 · ingestao   (data/raw -> bronze)", ingestao.main),
    ("2/5 · transformacao (bronze -> prata)", transformacao.main),
    ("3/5 · marts         (prata -> ouro)", marts.main),
    ("4/5 · auditoria     (descrições e datas)", auditoria.main),
    ("5/5 · qualidade     (checagens)", qualidade.main),
]


def main():
    """Roda as cinco etapas em ordem, parando na primeira que falhar."""
    for titulo, etapa in ETAPAS:
        print(f"\n=== {titulo} ===")
        etapa()
    print("\nPronto. Rode o dashboard com: uv run streamlit run app.py")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        print("\nPipeline interrompido: uma etapa encerrou com erro.", file=sys.stderr)
        raise
