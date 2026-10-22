import pandas as pd, sys, os
O=sys.argv[1]
def cat(p, idc):
    return set(pd.read_csv(os.path.join(O,p),sep=';',encoding='utf-8-sig',dtype=str)[idc].astype(int))
fk={'ID_ARTICULO':cat('01_Catalogo_Nucleo/01_Articulos.csv','ID_ARTICULO'),
 'ID_BATCH':cat('01_Catalogo_Nucleo/02_Batches.csv','ID_BATCH'),
 'ID_MUESTRA':cat('04_Catalogo_Muestra/06_Muestras_Batch.csv','ID_MUESTRA'),
 'ID_REINO':cat('02_Catalogo_Especie/01_Reinos.csv','ID_REINO'),'ID_FILO':cat('02_Catalogo_Especie/02_Filos.csv','ID_FILO'),
 'ID_CLASE_TAXONOMICA':cat('02_Catalogo_Especie/03_Clases_taxonomicas.csv','ID_CLASE_TAXONOMICA'),
 'ID_ORDEN':cat('02_Catalogo_Especie/04_Ordenes.csv','ID_ORDEN'),'ID_FAMILIA':cat('02_Catalogo_Especie/05_Familias.csv','ID_FAMILIA'),
 'ID_GENERO':cat('02_Catalogo_Especie/06_Generos.csv','ID_GENERO'),'ID_ESPECIE':cat('02_Catalogo_Especie/07_Especies.csv','ID_ESPECIE'),
 'ID_TIPO_MUESTRA':cat('04_Catalogo_Muestra/02_Tipos_muestra.csv','ID_TIPO_MUESTRA'),
 'ID_PARTE_ESTUDIADA':cat('04_Catalogo_Muestra/03_Partes_planta_estudiadas.csv','ID_PARTE_ESTUDIADA'),
 'ID_TIPO_CULTIVO':cat('04_Catalogo_Muestra/04_Tipos_cultivo.csv','ID_TIPO_CULTIVO'),
 'ID_METODO_EXTRACCION':cat('04_Catalogo_Muestra/05_Metodos_extraccion.csv','ID_METODO_EXTRACCION'),
 'ID_COLUMNA_CROMATOGRAFICA':cat('04_Catalogo_Muestra/01_Columnas_cromatograficas.csv','ID_COLUMNA_CROMATOGRAFICA'),
 'ID_MODO_IONIZACION':cat('01_Catalogo_Nucleo/03_Modo_ionizacion.csv','ID_MODO_IONIZACION'),
 'ID_NIVEL_IDENTIFICACION':cat('03_Catalogo_Metabolito/01_Niveles_identificacion.csv','ID_NIVEL_IDENTIFICACION'),
 'ID_SUPERCLASE_QUIMICA':cat('03_Catalogo_Metabolito/02_Superclases_quimicas.csv','ID_SUPERCLASE_QUIMICA'),
 'ID_CLASE_QUIMICA':cat('03_Catalogo_Metabolito/03_Clases_quimicas.csv','ID_CLASE_QUIMICA'),
 'ID_ADUCTO':cat('03_Catalogo_Metabolito/04_Aductos.csv','ID_ADUCTO'),
 'ID_METABOLITO':cat('03_Catalogo_Metabolito/05_Metabolitos.csv','ID_METABOLITO'),
 'ID_ACTIVIDAD_BIOLOGICA':cat('01_Catalogo_Nucleo/04_Actividades_biologicas.csv','ID_ACTIVIDAD_BIOLOGICA')}
bad=0; n=0
cols=None
fill={k:0 for k in fk}
for ch in pd.read_csv(os.path.join(O,'Dataset.csv'),sep=';',dtype=str,chunksize=1_000_000,keep_default_na=False):
    n+=len(ch)
    for k,s in fk.items():
        v=ch[k].astype(int)
        m=~v.isin(s)
        if m.any(): bad+=m.sum(); print('FK roto',k,v[m].unique()[:5])
        fill[k]+= (v!=0).sum()
    if cols is None:
        print(ch.head(3).T.to_string())
print('filas',n,'FK rotas',bad)
print({k:round(100*v/n,1) for k,v in fill.items()})
# pivote y muestras
mu=pd.read_csv(os.path.join(O,'04_Catalogo_Muestra/06_Muestras_Batch.csv'),sep=';',encoding='utf-8-sig',dtype=str)
for k,c in [('ID_ESPECIE','ID_ESPECIE'),('ID_PARTE_ESTUDIADA','ID_PARTE_ESTUDIADA'),('ID_TIPO_MUESTRA','ID_TIPO_MUESTRA'),('ID_TIPO_CULTIVO','ID_TIPO_CULTIVO'),('ID_METODO_EXTRACCION','ID_METODO_EXTRACCION'),('ID_BATCH','ID_BATCH')]:
    assert mu[c].astype(int).isin(fk[k]).all(), c
pv=pd.read_csv(os.path.join(O,'05_Pivotes/Registo_Actividades_biologicas.csv'),sep=';',encoding='utf-8-sig',dtype=str)
for k in ['ID_ARTICULO','ID_ESPECIE','ID_MUESTRA','ID_METABOLITO','ID_ACTIVIDAD_BIOLOGICA']:
    assert pv[k].astype(int).isin(fk[k]).all(), k
print('muestras y pivote OK')
