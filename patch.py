"""Gera versões das queries dos .pbix da Penalty sem as visitas de PESQUISA DE CAMPO zeradas."""
import re, os

SRC = r'C:\dev\news-penalty-trimestral\pbi_sql'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sql_ajustado')

# Visita zerada = pesquisa com formulário PESQUISA DE CAMPO (35/36) e nenhum espaço de share > 0.
HEADER = """-- AJUSTE PESQUISA DE CAMPO: visitas com o formulário PESQUISA DE CAMPO (35/36) em que o promotor
-- zerou as outras pesquisas (nenhum espaço de share > 0) saem da base deste BI.
IF OBJECT_ID('TEMPDB..#PESQ_ZERADA') IS NOT NULL DROP TABLE #PESQ_ZERADA;
SELECT DISTINCT PC.COD_PESQUISA
INTO #PESQ_ZERADA
FROM BI_F_FORMULARIO PC
WHERE PC.COD_FORMULARIO IN (35,36)
  AND NOT EXISTS (SELECT 1 FROM BI_F_SHARE SZ WHERE SZ.COD_PESQUISA = PC.COD_PESQUISA AND SZ.QTD_SHARE_MARCA > 0);

"""
ZERADAS = '(SELECT COD_PESQUISA FROM #PESQ_ZERADA)'
TAG = '/* AJUSTE PESQUISA DE CAMPO */'


def com_header(sql):
    m = re.match(r'\s*use\s+bi_cliente\s*\n', sql, flags=re.I)
    i = m.end() if m else 0
    return sql[:i] + HEADER + sql[i:]


def formulario(sql):
    return re.subn(r'(WHERE\s+F\.COD_FORMULARIO\s*=\s*\d+)',
                   rf'\1 {TAG}\n      AND F.COD_PESQUISA NOT IN {ZERADAS}', sql, flags=re.I)


def share(sql):
    return re.subn(r'(FROM\s+DBO\.BI_F_SHARE\s+AS\s+MP[\s\S]*?WHERE\s+1=1)',
                   rf'\1\n{TAG}\nAND MP.COD_PESQUISA NOT IN {ZERADAS}', sql, flags=re.I)


def ponto_extra(sql):
    return re.subn(r'(WHERE\s+)(pe\.cod_pessoa\s+not\s+in)',
                   rf'\1pe.COD_PESQUISA NOT IN {ZERADAS} {TAG}\n    AND \2', sql, flags=re.I)


def produto(sql):
    # toda leitura de BI_F_PRODUTO (inclusive as de ULT_COLETA/ULT_SEM/ULT_MES) passa pelo filtro,
    # senão a "última coleta" da loja continuaria apontando para a visita zerada
    filt = f'(SELECT * FROM BI_F_PRODUTO WHERE COD_PESQUISA NOT IN {ZERADAS})'

    def rep(m):
        alias = m.group(2) or ' BP'
        return f'{m.group(1)}{filt} {TAG}{alias}'
    return re.subn(r'(FROM\s+)BI_F_PRODUTO(\s+TAB\d)?(?=\s)', rep, sql, flags=re.I)


REGRAS = {
    'Share__f_share.sql': share, 'Share__f_produto.sql': produto,
    'Produtos__fProduto.sql': produto,
    'Execução_Bola__f_bola.sql': formulario, 'Execução_Bola__f_share.sql': share,
    'Execução_Calçados__f_calcados.sql': formulario, 'Execução_Calçados__f_share.sql': share,
    'Espaço_Loja__f_ponto_extra.sql': ponto_extra, 'Espaço_Loja__f_ponto_extra_dis.sql': ponto_extra,
    'One_Page__f_share.sql': share, 'One_Page__f_produto.sql': produto,
    'One_Page__f_ponto_extra.sql': ponto_extra, 'One_Page__f_bola.sql': formulario,
    'One_Page__f_calcados.sql': formulario, 'One_Page__f_treinamentos.sql': formulario,
    'Treinamento__f_treinamento.sql': formulario, 'Compre_e_Ganhe__f_treinamento.sql': formulario,
}

if __name__ == '__main__':
    for fn, fx in REGRAS.items():
        sql = open(os.path.join(SRC, fn), encoding='utf-8').read()
        new, n = fx(sql)
        assert n > 0, f'nenhum ponto de ajuste em {fn}'
        open(os.path.join(OUT, fn), 'w', encoding='utf-8').write(com_header(new))
        print(f'{fn:45s} {n} ajuste(s)')
