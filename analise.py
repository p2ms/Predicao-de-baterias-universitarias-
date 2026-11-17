import re, requests
from collections import Counter

H = {"User-Agent": "Mozilla/5.0 (pesquisa academica)"}
s = requests.get("https://platbu.com/sitemap.xml", headers=H, timeout=30)
urls = re.findall(r"<loc>(.*?)</loc>", s.text)
print("total de URLs:", len(urls))

# agrupa por primeiro segmento do caminho
grupos = Counter(u.replace("https://platbu.com", "").strip("/").split("/")[0] for u in urls)
print(grupos.most_common())

for g in ["baterias", "torneios", "sumulas", "jurados"]:
    ex = [u for u in urls if f"/{g}/" in u][:3]
    print(g, ex)