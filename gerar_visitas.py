"""Gera visitas_pesquisa_campo_<data>.csv: uma linha por visita com PESQUISA DE CAMPO (forms 35/36),
comparando estoque/share/ponto extra com a visita anterior da mesma loja.
STATUS: ZERADA (nenhum share > 0, sai dos BIs pela regra) / REVISAR (tem share, mas bola ou calçado
zerou com anterior > 0) / OK."""
import datetime
import sys
import pandas as pd
import pyodbc

CS = ("DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:SEU_SERVIDOR_SQL,1433;DATABASE=bi_cliente;"
      "Trusted_Connection=yes;TrustServerCertificate=yes")
SQL = """
WITH V AS (SELECT COD_LOJA, COD_PESQUISA, MIN(DATA) DATA, MAX(COD_FORMULARIO) FORM, MAX(COD_PESSOA) COD_PESSOA
           FROM bi_f_formulario WHERE COD_FORMULARIO IN (35,36) GROUP BY COD_LOJA, COD_PESQUISA),
PR AS (SELECT COD_LOJA, COD_PESQUISA, MIN(DATA) DATA,
              SUM(CASE WHEN COD_CATEGORIA=2 THEN ESTOQUE ELSE 0 END) EB,
              SUM(CASE WHEN COD_CATEGORIA=4 THEN ESTOQUE ELSE 0 END) EC
       FROM bi_f_produto GROUP BY COD_LOJA, COD_PESQUISA),
SH AS (SELECT COD_LOJA, COD_PESQUISA, MIN(DATA) DATA,
              SUM(CASE WHEN COD_CATEGORIA=2 THEN QTD_SHARE_MARCA ELSE 0 END) SB,
              SUM(CASE WHEN COD_CATEGORIA=4 THEN QTD_SHARE_MARCA ELSE 0 END) SC
       FROM bi_f_share GROUP BY COD_LOJA, COD_PESQUISA),
PE AS (SELECT COD_LOJA, COD_PESQUISA, MIN(DATA) DATA, SUM(CAST(FL_EXISTE AS int)) PX
       FROM bi_f_ponto_extra GROUP BY COD_LOJA, COD_PESQUISA)
SELECT v.COD_LOJA, l.NOM_FANTASIA LOJA, l.DES_BANDEIRA BANDEIRA, l.DES_CIDADE CIDADE, l.DES_UF UF,
       v.DATA, v.COD_PESQUISA, v.FORM, p.NOM_PESSOA PROMOTOR, p.SUPERVISOR,
       pr.EB ESTOQUE_BOLA, pra.EB ESTOQUE_BOLA_ANT, pr.EC ESTOQUE_CALC, pra.EC ESTOQUE_CALC_ANT,
       sh.SB SHARE_BOLA_TOT, sha.SB SHARE_BOLA_TOT_ANT, sh.SC SHARE_CALC_TOT, sha.SC SHARE_CALC_TOT_ANT,
       pe.PX PONTO_EXTRA, pea.PX PONTO_EXTRA_ANT
FROM V v
LEFT JOIN bi_d_loja l ON l.COD_LOJA=v.COD_LOJA AND l.date_to>'2100-01-01'
LEFT JOIN bi_d_pessoa p ON p.COD_PESSOA=v.COD_PESSOA AND p.date_to>'2100-01-01'
LEFT JOIN PR pr ON pr.COD_LOJA=v.COD_LOJA AND pr.COD_PESQUISA=v.COD_PESQUISA
LEFT JOIN SH sh ON sh.COD_LOJA=v.COD_LOJA AND sh.COD_PESQUISA=v.COD_PESQUISA
LEFT JOIN PE pe ON pe.COD_LOJA=v.COD_LOJA AND pe.COD_PESQUISA=v.COD_PESQUISA
OUTER APPLY (SELECT TOP 1 * FROM PR x WHERE x.COD_LOJA=v.COD_LOJA AND x.COD_PESQUISA<v.COD_PESQUISA
             AND x.COD_PESQUISA NOT IN (SELECT COD_PESQUISA FROM V) ORDER BY x.DATA DESC, x.COD_PESQUISA DESC) pra
OUTER APPLY (SELECT TOP 1 * FROM SH x WHERE x.COD_LOJA=v.COD_LOJA AND x.COD_PESQUISA<v.COD_PESQUISA
             AND x.COD_PESQUISA NOT IN (SELECT COD_PESQUISA FROM V) ORDER BY x.DATA DESC, x.COD_PESQUISA DESC) sha
OUTER APPLY (SELECT TOP 1 * FROM PE x WHERE x.COD_LOJA=v.COD_LOJA AND x.COD_PESQUISA<v.COD_PESQUISA
             AND x.COD_PESQUISA NOT IN (SELECT COD_PESQUISA FROM V) ORDER BY x.DATA DESC, x.COD_PESQUISA DESC) pea
"""


def status(r):
    if not ((r.SHARE_BOLA_TOT or 0) > 0 or (r.SHARE_CALC_TOT or 0) > 0):
        return 'ZERADA - sai dos BIs'
    if ((r.ESTOQUE_BOLA or 0) == 0 and (r.ESTOQUE_BOLA_ANT or 0) > 0) or \
       ((r.ESTOQUE_CALC or 0) == 0 and (r.ESTOQUE_CALC_ANT or 0) > 0):
        return 'REVISAR - parcial'
    return 'OK - mantida'


if __name__ == '__main__':
    d = pd.read_sql(SQL, pyodbc.connect(CS, timeout=30))
    d['LOJA'] = d['LOJA'].str.replace('&amp;', '&', regex=False)
    d.insert(10, 'STATUS', d.apply(status, axis=1))
    d = d.sort_values(['DATA', 'COD_LOJA'])
    out = sys.argv[1] if len(sys.argv) > 1 else f'visitas_pesquisa_campo_{datetime.date.today()}.csv'
    d.to_csv(out, sep=';', decimal=',', index=False, encoding='utf-8-sig', float_format='%.1f')
    print(len(d), 'visitas,', d.COD_LOJA.nunique(), 'lojas ->', out)
    print(d.STATUS.value_counts().to_string())
