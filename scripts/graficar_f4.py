"""Diagramas de calibración de F4 a partir de bins verificados."""
import csv
import json
from collections import defaultdict

from eda_f3 import svg
from experimento_f4 import OUT, ROOT, file_hash


def draw(model, rows, destination):
    groups=defaultdict(list)
    for r in rows:
        groups[r["competicion"], r["clase"], r["version"]].append(r)
    competitions=("*","BL1","CL","FL1","PD","PL","SA")
    parts=[]
    for i,comp in enumerate(competitions):
        parts.append(f'<text x="26" y="{157+i*134}" font-size="13">{comp if i else "Total"}</text>')
        for j,klass in enumerate("1X2"):
            x,y=100+j*260,83+i*134
            size=96
            parts.append(f'<text x="{x+109}" y="{y+13}" font-size="12">{klass}</text>')
            parts.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" stroke="#b4c3cb"/>')
            parts.append(f'<path d="M {x} {y+size} L {x+size} {y}" stroke="#9a9fa4" fill="none"/>')
            for version,color in (("bruta","#176a8c"),("temperatura","#a64830")):
                for r in groups.get((comp,klass,version),[]):
                    xx=x+size*float(r["pronostico"])
                    yy=y+size*(1-float(r["observado"]))
                    lo=y+size*(1-float(r["wilson_inf"]))
                    hi=y+size*(1-float(r["wilson_sup"]))
                    n=int(r["n"])
                    parts.append(f'<line x1="{xx}" x2="{xx}" y1="{lo}" y2="{hi}" stroke="{color}" opacity=".45"/>')
                    parts.append(f'<circle cx="{xx}" cy="{yy}" r="{2+min(n,100)/40}" fill="{color}">'
                                 f'<title>{version}, n={n}</title></circle>')
    svg(f"Calibración 1X2 · {model}",
        "X: probabilidad, Y: frecuencia, [0,1] · azul: bruta, rojo: temperatura · intervalos Wilson descriptivos",
        "".join(parts),destination,width=790,height=1025)


def main():
    manifest=json.loads((OUT/"MANIFIESTO_F4.json").read_text(encoding="utf-8"))
    source=OUT/"calibracion_bins.csv"
    if file_hash(source)!=manifest["archivos"][source.name]:
        raise ValueError("Archivo de calibración distinto del manifiesto")
    with source.open(encoding="utf-8",newline="") as handle:
        rows=list(csv.DictReader(handle))
    dest=ROOT/"docs"/"calibracion_f4"
    dest.mkdir(exist_ok=True)
    hashes={}
    for model in sorted({r["modelo"] for r in rows}):
        chart=dest/(model+".svg")
        draw(model,[r for r in rows if r["modelo"]==model],chart)
        hashes[chart.name]=file_hash(chart)
    provenance=dict(entrada_sha256=file_hash(source),codigo_sha256=file_hash(ROOT/"scripts/graficar_f4.py"),archivos=hashes)
    (dest/"MANIFIESTO_GRAFICAS.json").write_text(json.dumps(provenance,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
