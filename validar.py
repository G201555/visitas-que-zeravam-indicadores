import pyodbc, os, time, sys
from patch import REGRAS, SRC, OUT
CS = ("DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:SEU_SERVIDOR_SQL,1433;DATABASE=bi_cliente;Trusted_Connection=yes;TrustServerCertificate=yes")
def run(path):
    t=time.time(); cn = pyodbc.connect(CS, timeout=30, autocommit=True); c = cn.cursor(); c.execute(open(path, encoding='utf-8').read()); n=None; cols=None
    while True:
        if c.description:
            cols=[d[0] for d in c.description]; n=0; ult=0
            iu = cols.index('ULT_COLETA') if 'ULT_COLETA' in cols else None
            while True:
                rows=c.fetchmany(50000)
                if not rows: break
                n+=len(rows)
                if iu is not None: ult+=sum(r[iu] for r in rows)
        if not c.nextset(): break
    return n, (ult if iu is not None else None), time.time()-t
if __name__ == '__main__':
  for fn in (sys.argv[1:] or REGRAS):
    a = run(os.path.join(SRC, fn)); b = run(os.path.join(OUT, fn))
    extra = f' | ULT_COLETA {a[1]} -> {b[1]}' if a[1] is not None else ''
    print(f'{fn:42s} linhas {a[0]:>9,} -> {b[0]:>9,} (-{a[0]-b[0]:,})  tempo {a[2]:.0f}s / {b[2]:.0f}s{extra}', flush=True)
