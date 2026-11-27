import json, os, platform, subprocess, sys, time, pathlib, statistics
from datetime import datetime, timezone
from importlib.metadata import version
root=pathlib.Path(__file__).resolve().parents[2]; out=pathlib.Path(sys.argv[1]).resolve(); out.mkdir(parents=True,exist_ok=True); rows=[]
if any(out.glob("benchmark_pair_run_*.json")): raise FileExistsError("Choose a fresh output directory")
ref=json.loads((root/'docs/data/observed_alentejo_soil5_pair_20261123.json').read_text())
for i in range(3):
 dst=out/f'benchmark_pair_run_{i+1}.json'; t=time.perf_counter(); row={'repeat':i+1,'cache':'new Python process; OS/provider caches uncontrolled'}
 try:
  r=subprocess.run([sys.executable,str(root/'research/prototypes/soil_surface_pair_public_preview.py'),'--out',str(dst)],capture_output=True,text=True,timeout=65); row.update(seconds=round(time.perf_counter()-t,3),exit_code=r.returncode)
  if r.returncode==0:
   d=json.loads(dst.read_text()); row.update(cells=d['qa_valid_overlap_grid_pixels'],checksum_matches=d['analytical_array_sha256']==ref['analytical_array_sha256'],scenes_match=d['scenes']==ref['scenes'])
  else: row['error']=r.stderr[-500:]
 except subprocess.TimeoutExpired: row.update(seconds=round(time.perf_counter()-t,3),error='timeout')
 rows.append(row); print(row,flush=True)
 report={'date':datetime.now(timezone.utc).isoformat(),'workload':'Existing real two-scene Alentejo Sentinel-2 optical preview, 96x96 grid, 5 assets per scene','software':{x:version(x) for x in ['numpy','rasterio','pystac-client','planetary-computer']},'python':platform.python_version(),'os':platform.system()+' '+platform.release(),'logical_cpu_count':os.cpu_count(),'runs':rows,'limitations':'End-to-end elapsed time only, provider/network/cache uncontrolled; not API scalability or independent scientific validation.'}
 good=[r['seconds'] for r in rows if r.get('exit_code')==0 and r.get('checksum_matches')]; report['summary']={'successful_repeats':len(good),'median_seconds':statistics.median(good) if good else None,'min_seconds':min(good) if good else None,'max_seconds':max(good) if good else None}; (out/'benchmark_pair_report.json').write_text(json.dumps(report,indent=2));
