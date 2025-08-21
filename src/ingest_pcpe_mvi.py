from pathlib import Path
import pandas as pd
import numpy as np
import re, unicodedata

RAW = Path("data/raw")
PROC = Path("data/processed"); PROC.mkdir(parents=True, exist_ok=True)

def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s

def flatten_columns(cols):
    if isinstance(cols, pd.MultiIndex):
        flat = []
        for tup in cols:
            parts = [str(x) for x in tup if str(x) != "nan"]
            name = "_".join(parts) if parts else "col"
            flat.append(name)
        return flat
    return list(cols)

def detect_header_row(df_preview):
    """Encontra a linha que parece conter o cabeçalho (município + data/ano/mes/competencia)."""
    for r in range(min(20, len(df_preview))):
        row = df_preview.iloc[r].astype(str).tolist()
        row_norm = [normalize(x) for x in row]
        has_muni = any("munic" in c for c in row_norm)
        has_time = any(k in "_".join(row_norm) for k in ["data","ano","mes","competencia","periodo","mes_ano","mesano"])
        if has_muni and has_time:
            return r

    r0 = df_preview.iloc[0].astype(str).tolist()
    if any("munic" in normalize(x) for x in r0):
        return 0
    return None

def month_name_to_num(x):
    if pd.isna(x): return np.nan
    s = normalize(x)
    mapa = {"jan":1,"janeiro":1,"fev":2,"fevereiro":2,"mar":3,"marco":3,"abr":4,"abril":4,"mai":5,"maio":5,
            "jun":6,"junho":6,"jul":7,"julho":7,"ago":8,"agosto":8,"set":9,"setembro":9,"out":10,"outubro":10,
            "nov":11,"novembro":11,"dez":12,"dezembro":12}
    for k,v in mapa.items():
        if k in s: return v
    m = re.search(r"\b(1[0-2]|[1-9])\b", s)
    return int(m.group(1)) if m else np.nan

def build_date(df):
    cols = set(df.columns)
    data_cols = [c for c in df.columns if "data" in c]
    ano_cols  = [c for c in df.columns if c=="ano" or c.endswith("_ano")]
    mes_cols  = [c for c in df.columns if c in ("mes","mes_num","numero_mes","nr_mes","mesref","mes_referencia")]
    comb_cols = [c for c in df.columns if any(k in c for k in ["competencia","periodo","mes_ano","mesano","mes_e_ano"])]

    if data_cols:
        dcol = data_cols[0]
        d = pd.to_datetime(df[dcol], errors="coerce", dayfirst=True)
        if d.notna().mean() > 0.5:
            return d

    if ano_cols and mes_cols:
        a, m = ano_cols[0], mes_cols[0]
        A = pd.to_numeric(df[a], errors="coerce")
        M = pd.to_numeric(df[m], errors="coerce")
        return pd.to_datetime(dict(year=A, month=M, day=1), errors="coerce")

    if ano_cols:
        a = ano_cols[0]
        # tentar algum campo com nome de mês (texto)
        mes_nome_cols = [c for c in df.columns if "mes" in c and c not in mes_cols]
        if mes_nome_cols:
            mn = mes_nome_cols[0]
            A = pd.to_numeric(df[a], errors="coerce")
            M = df[mn].map(month_name_to_num)
            return pd.to_datetime(dict(year=A, month=M, day=1), errors="coerce")

    if comb_cols:
        c = comb_cols[0]
        d = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
        if d.notna().mean() < 0.8:
            ano = df[c].astype(str).str.extract(r"(20\\d{2}|19\\d{2})", expand=False)
            mes_text = df[c].astype(str)
            mes_num = mes_text.map(month_name_to_num)
            mes_num = mes_num.fillna(pd.to_numeric(mes_text.str.extract(r"(\\d{1,2})", expand=False), errors="coerce"))
            d = pd.to_datetime(dict(year=pd.to_numeric(ano, errors="coerce"), month=mes_num, day=1), errors="coerce")
        return d

    return pd.Series(pd.NaT, index=df.index)

matches = list(RAW.glob("MICRODADOS_DE_MVI*.xlsx"))
if not matches:
    raise FileNotFoundError("Coloque o XLSX em data/raw/ (ex.: MICRODADOS_DE_MVI_JAN_2004_A_JUL_2025.xlsx)")
xlsx_path = matches[0]

# varre as abas e acha uma com cabeçalho válido
xls = pd.ExcelFile(xlsx_path)
chosen = None
header_row = None

for sheet in xls.sheet_names:
    preview = pd.read_excel(xlsx_path, sheet_name=sheet, header=None, nrows=20)
    hr = detect_header_row(preview)
    if hr is None:
        continue
    df = pd.read_excel(xlsx_path, sheet_name=sheet, header=hr)
    # lidar com multiindex / unnamed
    df.columns = flatten_columns(df.columns)
    # substituir "Unnamed" por nomes simples
    df.columns = [("col_"+str(i) if str(c).lower().startswith("unnamed") else str(c)) for i,c in enumerate(df.columns)]
    # normalizar
    df.columns = [normalize(c) for c in df.columns]

    # critérios mínimos: ter algo de município e tempo
    has_muni = any("munic" in c for c in df.columns)
    has_time = any(c in df.columns for c in ["data","ano","mes","competencia","periodo","mes_ano","mesano"])
    if has_muni and has_time:
        chosen = df
        header_row = hr
        print(f">> Planilha escolhida: '{sheet}' (cabeçalho na linha {hr})")
        break

if chosen is None:
    raise ValueError("Não encontrei uma aba com cabeçalho contendo MUNICÍPIO e DATA/ANO/MÊS/COMPETÊNCIA.")

df = chosen.copy()

print(">> Colunas detectadas (normalizadas):")
print(df.columns[:30].tolist(), "..." if len(df.columns)>30 else "")

# identifica colunas de interesse
muni_candidates = [c for c in df.columns if "munic" in c]
if not muni_candidates:
    raise ValueError("Não encontrei coluna de município.")
municipio_col = muni_candidates[0]

mvi_candidates = [c for c in df.columns if c in ("total_de_vitimas","mvi","vitimas","total","qtd","quantidade")]
if mvi_candidates:
    mvi_col = mvi_candidates[0]
else:
    df["mvi"] = 1
    mvi_col = "mvi"

# monta coluna data
df["data"] = build_date(df)
if df["data"].isna().all():
    raise ValueError("Não consegui inferir a coluna de DATA. Reveja o arquivo (COMPETÊNCIA/ANO/MÊS).")

# limpa e agrega
df = df[[municipio_col, "data", mvi_col]].dropna(subset=[municipio_col, "data"]).copy()
df[mvi_col] = pd.to_numeric(df[mvi_col], errors="coerce").fillna(0).astype(int)
df["ano"] = df["data"].dt.year
df["mes"] = df["data"].dt.month

monthly = (
    df.groupby([municipio_col, "ano", "mes"], as_index=False)
      .agg(mvi=(mvi_col, "sum"))
      .sort_values([municipio_col, "ano", "mes"])
).rename(columns={municipio_col: "municipio"})

# monta features e rótulo
def add_features(g):
    g = g.copy()
    g["date"] = pd.to_datetime(dict(year=g["ano"], month=g["mes"], day=1))
    g["lag1"] = g["mvi"].shift(1)
    g["ma3"]  = g["mvi"].rolling(3).mean().shift(1)
    g["ma6"]  = g["mvi"].rolling(6).mean().shift(1)
    g["chg"]  = g["mvi"].pct_change().shift(1)
    p75 = g["mvi"].quantile(0.75)
    g["alto_risco_mvi_next"] = (g["mvi"].shift(-1) >= p75).astype(int)
    g["mes_sin"] = np.sin(2*np.pi*(g["mes"]/12.0))
    g["mes_cos"] = np.cos(2*np.pi*(g["mes"]/12.0))
    return g

feat = monthly.groupby("municipio", group_keys=False).apply(add_features)
feat = feat.dropna(subset=["lag1","ma3","ma6","chg","alto_risco_mvi_next"])

out = PROC / "mvi_pe_features.csv"
feat.to_csv(out, index=False, encoding="utf-8")
print(f"OK -> {out} ({len(feat)} linhas, {feat['municipio'].nunique()} municípios)")
