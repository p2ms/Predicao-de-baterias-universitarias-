import re, time, pathlib
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://platbu.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (pesquisa academica)"}
CACHE = pathlib.Path("cache")
CACHE.mkdir(exist_ok=True)


def baixar(path):
    arq = CACHE / (re.sub(r"[^\w\-]", "_", path.strip("/")) or "home")
    if arq.exists():
        return arq.read_text(encoding="utf-8")
    r = requests.get(BASE + path, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    arq.write_text(r.text, encoding="utf-8")
    time.sleep(1)
    return r.text


def tabela_com_links(html):
    soup = BeautifulSoup(html, "html.parser")
    tab = soup.find("table")
    if tab is None:
        return None
    linhas = tab.find_all("tr")
    cab = [c.get_text(strip=True) for c in linhas[0].find_all(["th", "td"])]
    dados = []
    for tr in linhas[1:]:
        cel = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
        a = tr.find("a", href=True)
        dados.append(cel + [a["href"] if a else None])
    df = pd.DataFrame(dados)
    nomes = cab + ["link"]
    if len(nomes) == df.shape[1]:
        df.columns = nomes
    return df


def coletar(paths, nome_coluna):
    partes, sem_tabela, falhas = [], [], []
    for i, p in enumerate(paths, 1):
        try:
            df = tabela_com_links(baixar(p))
            if df is None or df.empty:
                sem_tabela.append(p)
            else:
                df.insert(0, nome_coluna, p.rstrip("/").split("/")[-1])
                df.insert(1, "pagina", p)
                partes.append(df)
        except Exception as e:
            falhas.append((p, repr(e)))
        if i % 25 == 0:
            print(f"{i}/{len(paths)}")
    print(f"{len(partes)} com tabela | {len(sem_tabela)} sem tabela | {len(falhas)} falhas")
    if falhas:
        print("primeiras falhas:", falhas[:5])
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


# URLs a partir do sitemap
sm = requests.get(BASE + "/sitemap.xml", headers=HEADERS, timeout=30).text
urls = re.findall(r"<loc>(.*?)</loc>", sm)
paths = [u.replace("https://platbu.com", "") for u in urls]

p_bat = sorted({p for p in paths if re.fullmatch(r"/baterias/[\w\-]+", p)})
p_tor = sorted({p for p in paths if p.startswith("/torneios/")})
print(len(p_bat), "baterias |", len(p_tor), "páginas de torneios")
print("exemplos torneios:", p_tor[:5])

df_bat = coletar(p_bat, "bateria_slug")
print(df_bat.shape)
df_bat.to_csv("participacoes_por_bateria.csv", index=False, encoding="utf-8-sig")

df_tor = coletar(p_tor, "torneio_slug")
print(df_tor.shape)
df_tor.to_csv("resultados_por_torneio.csv", index=False, encoding="utf-8-sig")