# Limites estaduais usados no mapa

Origem: [Click That Hood / Code for Germany](https://github.com/codeforgermany/click_that_hood/blob/main/public/data/brazil-states.geojson).
Licença do repositório de origem: MIT, reproduzida em `LICENCA-mapa.txt`.

Arquivo de origem obtido em 01/11/2026, com SHA-256 `f73a5975de5552ffa24d02cab89a07f444e3035a5f8e05943cba844ce0153f1e`.
A cópia local mantém as 27 UFs e os nomes de origem. Geometrias foram
simplificadas com tolerância de 0,01 grau, preservando a topologia de cada
feição para a visualização nacional. Feições originalmente inválidas foram
reparadas com `make_valid` antes da simplificação (CE, MA, MT, PA, RJ, RO, RR,
RS, SC, SP e TO). A maior diferença relativa de área após simplificar foi
inferior a 0,27%, medida em coordenadas geográficas apenas como controle técnico.
As coordenadas foram arredondadas a cinco casas, mantendo a validade das feições.
Não é uma malha oficial atualizada nem um arquivo para análise geoespacial.
A simplificação é apenas visual; não modifica os indicadores ou a associação por UF.

O GeoJSON é embutido na figura e o mapa usa fundo branco sem tiles, tokens ou
consulta à URL remota de geometria na abertura do dashboard. O componente
interativo ainda requer JavaScript e suporte WebGL do navegador.
