# Visitas que zeravam indicadores

Investigação e correção de um problema de qualidade de dados em produção.

## O problema

Um formulário novo foi incluído nas visitas de campo. Em parte dessas visitas, o promotor respondeu zero em todas as outras pesquisas da mesma visita: share, estoque, ponto extra e treinamento. Os relatórios de Power BI passaram a mostrar quedas que não existiam.

## Como resolvi

1. **Achei o padrão** comparando cada visita com a anterior da mesma loja (`gerar_visitas.py`) e classificando em ZERADA, REVISAR e OK.
2. **Escrevi uma regra dinâmica** em vez de uma lista fixa: a visita sai dos relatórios quando tem o formulário novo e nenhum registro de share maior que zero. Assim a regra também pega os casos futuros.
3. **Apliquei a regra** nas queries de todos os relatórios afetados de forma automática (`patch.py`).
4. **Validei** rodando a query original e a ajustada e comparando o resultado (`validar.py`).

## O que vale olhar

- Diagnóstico a partir do dado, não de suposição.
- Regra que se mantém sozinha, sem manutenção manual.
- Validação antes e depois em cada relatório.

## Stack

Python, pandas, pyodbc, SQL Server (T-SQL), Power Query.

---
Projeto feito no trabalho, publicado sem dados do cliente.
