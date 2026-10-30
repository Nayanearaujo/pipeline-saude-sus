"""
Executa o pipeline inteiro numa tacada: bronze -> prata -> ouro -> qualidade.

Atalho para o corretor e para o dia a dia. Pressupoe que os dados ja estao em
data/raw/ (rode antes baixar_dados.py e gerar_dicionarios.py). Para o painel,
rode depois: uv run streamlit run app.py

    uv run python executar.py
"""
import sys

from pipeline import ingestao, marts, qualidade, transformacao

ETAPAS = [
    ("1/4 · ingestao   (data/raw -> bronze)", ingestao.main),
    ("2/4 · transformacao (bronze -> prata)", transformacao.main),
    ("3/4 · marts         (prata -> ouro)", marts.main),
    ("4/4 · qualidade     (checagens)", qualidade.main),
]


def main():
    """Roda as quatro etapas em ordem, parando na primeira que falhar."""
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
