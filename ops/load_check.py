#!/usr/bin/env python3
"""Small, explicitly requested load check against an operator-supplied URL."""
import argparse
import concurrent.futures
import statistics
import time
from urllib.request import urlopen
parser=argparse.ArgumentParser()
parser.add_argument('url'); parser.add_argument('--requests',type=int,default=60); parser.add_argument('--concurrency',type=int,default=4)
args=parser.parse_args()
if not 1 <= args.requests <= 10000 or not 1 <= args.concurrency <= 32:
    raise SystemExit('Use 1-10000 requests and 1-32 concurrent workers.')
def one(_):
    start=time.perf_counter()
    with urlopen(args.url,timeout=20) as response:
        response.read(); assert response.status==200
    return time.perf_counter()-start
with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
    values=sorted(pool.map(one,range(args.requests)))
print(f'Completed={len(values)} mean={statistics.mean(values):.3f}s p95={values[min(len(values)-1,int(len(values)*.95))]:.3f}s max={max(values):.3f}s')
