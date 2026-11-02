# Entrega do projeto de engenharia de dados

**Autora:** Nayane Araújo, pós-graduanda em Engenharia de Dados.

**Tema:** registros públicos de internação hospitalar do SIH/SUS.
**Competência de processamento:** abril de 2026.
**Abrangência:** Brasil, por residência registrada.

## Acessos

- [Repositório](https://github.com/Nayanearaujo/pipeline-saude-sus)
- [Painel em Streamlit](https://pipeline-saude-sus.streamlit.app/)
- [Relatório executivo](https://nayanearaujo.github.io/pipeline-saude-sus/relatorio.html)
- [Guia do projeto](https://nayanearaujo.github.io/pipeline-saude-sus/)
- [Definições dos indicadores](indicadores.md)
- [Validação e limites](VALIDACAO.md)

## Escopo implementado

| Componente | Entrega |
|---|---|
| Fonte própria | SIH/SUS, com 1.238.763 registros brutos de internação |
| Arquitetura | Bronze, Prata e Ouro em DuckDB |
| Relacionamentos | Internações, CID, municípios e unidades federativas |
| Transformação | Tipos explícitos, deduplicação e decodificação dos campos |
| Camada analítica | Dez marts SQL com grão declarado |
| Qualidade | 37 regras e reconciliação entre camadas e agregados |
| Testes | 145 testes, cobertura de 97,01% e mínimo de 95% no CI |
| Apresentação | Cinco cartões, nove figuras, painel interativo e relatório HTML |
| Reprodutibilidade | Dependências versionadas, execução documentada e conferência isolada |

Os CSVs publicados contêm 1.238.234 AIHs e R$ 2.258.865.118,36.
A execução local registrada excluiu 529 duplicatas, nenhuma linha por ausência
de valor e aprovou as 37 regras. Os dez marts somam 16.400 linhas.

A série diária contém 703.067 entradas em abril. As demais 535.167 entradas têm
datas anteriores, conforme o histograma da execução local. Todos os registros
brutos têm competência abril de 2026.

## Conferência antes da apresentação

A conferência local final aprovou os 145 testes, as 37 regras e a igualdade dos
dez marts. O valor exato com centavos foi confirmado. A correção de idade ignorada
não alterou os agregados deste conjunto.

A instância pública do Streamlit deve exibir os nove gráficos, os dois seletores
e o detalhamento expansível do perfil. A interface antiga observada no navegador
remoto não foi considerada prova de atualização do deploy.

O procedimento completo está em [CONFERENCIA_LOCAL.md](CONFERENCIA_LOCAL.md).
Não é necessário publicar o banco, os microdados ou configurações privadas.
