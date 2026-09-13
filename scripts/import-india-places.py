"""Refresh GeoNames India populated places. No thermal data is fetched."""
import io, json, zipfile, urllib.request, gzip
from pathlib import Path
from datetime import date
BASE = 'https://download.geonames.org/export/dump/'
def download(name):
    with urllib.request.urlopen(BASE + name, timeout=120) as r: return r.read()
admin = {}
for line in download('admin1CodesASCII.txt').decode('utf-8').splitlines():
    f = line.split('\t')
    if f[0].startswith('IN.'): admin[f[0].split('.')[1]] = f[1]
archive = zipfile.ZipFile(io.BytesIO(download('IN.zip')))
rows = []
for line in archive.read('IN.txt').decode('utf-8').splitlines():
    f = line.split('\t')
    if f[6] != 'P' or f[7] in ('PPLH','PPLQ','PPLW','PPLCH'): continue
    rows.append([int(f[0]), f[2] or f[1], admin.get(f[10], 'Unspecified region'), float(f[4]), float(f[5]), int(f[14]), f[7], f[3]])
rows.sort(key=lambda r: (-r[5], r[1], r[0]))
out=Path('public/data');out.mkdir(parents=True,exist_ok=True)
payload = json.dumps({'source':'GeoNames','sourceUrl':BASE+'IN.zip','license':'CC BY 4.0','downloaded':str(date.today()),'coverage':'GeoNames populated places in India, including cities, towns and villages; not an exhaustive official city register. Historical, abandoned and destroyed settlements excluded.','fields':['id','name','region','latitude','longitude','population','featureCode','aliases'],'places':rows},ensure_ascii=False,separators=(',',':')).encode('utf-8')
with gzip.GzipFile(filename=str(out/'india-places.json.gz'), mode='wb', mtime=0) as f: f.write(payload)
print(f'{len(rows):,} places; {len(set(r[2] for r in rows))} regions; {(out/"india-places.json.gz").stat().st_size:,} bytes')
