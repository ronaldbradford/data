#!/usr/bin/env python
import pandas as pd
import sys


def usage():
  print(f"USAGE: {sys.argv[0]} <file>.parquet")
  sys.exit(1)

if len(sys.argv) == 1:
  usage()

df = pd.read_parquet(sys.argv[1])
df.to_csv(sys.argv[1].replace("parquet","tsv"), sep='\t')
