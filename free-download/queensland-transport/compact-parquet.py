#!/usr/bin/env python
"""Compact the many small Parquet files in each partition into one.

write-translink-to-parquet.py adds a new part-*.parquet file per flush, so a
short --max-age leaves each dt=<date>/region=<region>/ directory holding many
small files, which slows every reader. This merges each partition's files
into a single compact-<timestamp>.parquet, dropping exact (vehicle_id, ts)
repeats and sorting by (vehicle_id, ts) so Parquet min/max statistics are
effective.

The merged file is written under a dot-prefixed temp name and renamed into
place (like the collector), and the source files are deleted only after the
output has been verified, so readers never see a half-written file. Between
the rename and the deletes a reader can briefly see rows twice, which the
viewer and --summary both tolerate.

Today's partition (UTC) is skipped by default because the collector is still
appending to it; pass --include-today to compact it anyway.

Requires: pip install duckdb pyarrow

Examples:
    ./compact-parquet.py --dry-run
    ./compact-parquet.py
    ./compact-parquet.py --root positions --min-files 5 --include-today
"""

import argparse
import glob
import os
import sys
import time
from datetime import datetime, timezone

import duckdb
import pyarrow.parquet as pq

QUERY = """
SELECT * FROM read_parquet({files}, union_by_name = true)
QUALIFY row_number() OVER (PARTITION BY vehicle_id, ts ORDER BY fetched_at) = 1
ORDER BY vehicle_id, ts
"""


def source_files(directory):
    """Finished Parquet files in a partition (temp files are dot-prefixed)."""
    return sorted(path for path in glob.glob(os.path.join(directory, "*.parquet"))
                  if not os.path.basename(path).startswith("."))


def compact_partition(connection, directory, compression):
    """Merge a partition's files into one. Returns (rows_in, rows_out, name)."""
    files = source_files(directory)
    rows_in = sum(pq.ParquetFile(path).metadata.num_rows for path in files)

    schema = pq.read_schema(files[0])  # keep the collector's column types
    table = connection.sql(QUERY.format(files=repr(files))).arrow()
    if hasattr(table, "read_all"):  # newer duckdb returns a RecordBatchReader
        table = table.read_all()
    table = table.select(schema.names).cast(schema)

    name = "compact-%d-%d.parquet" % (int(time.time()), os.getpid())
    final_path = os.path.join(directory, name)
    temp_path = os.path.join(directory, "." + name + ".tmp")

    pq.write_table(table, temp_path, compression=compression)
    written = pq.ParquetFile(temp_path).metadata.num_rows
    if written != table.num_rows:
        os.remove(temp_path)
        raise RuntimeError("row count mismatch writing %s" % final_path)
    os.replace(temp_path, final_path)

    for path in files:
        os.remove(path)
    return rows_in, written, name


def main():
    parser = argparse.ArgumentParser(
        description="Merge the small Parquet files in each partition of the "
                     "dataset built by write-translink-to-parquet.py.")
    parser.add_argument("--root", default="positions",
                        help="dataset root directory (default: positions)")
    parser.add_argument("--min-files", type=int, default=2,
                        help="skip partitions with fewer files than this "
                             "(default: 2)")
    parser.add_argument("--include-today", action="store_true",
                        help="also compact today's (UTC) partition, which the "
                             "collector may still be writing to")
    parser.add_argument("--compression", default="zstd",
                        choices=("zstd", "snappy", "gzip", "none"),
                        help="Parquet compression codec (default: zstd)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be merged without changing anything")
    args = parser.parse_args()

    if not os.path.isdir(args.root):
        parser.error("%r does not exist" % args.root)

    today = datetime.now(timezone.utc).strftime("dt=%Y-%m-%d")
    connection = duckdb.connect()
    merged = 0

    for directory in sorted(glob.glob(os.path.join(args.root, "dt=*", "region=*"))):
        partition = os.path.relpath(directory, args.root)
        if partition.split(os.sep)[0] == today and not args.include_today:
            print("%-32s skipped (today; use --include-today)" % partition)
            continue
        count = len(source_files(directory))
        if count < args.min_files:
            continue
        if args.dry_run:
            print("%-32s would merge %d files" % (partition, count))
            continue
        rows_in, rows_out, name = compact_partition(
            connection, directory, args.compression)
        merged += 1
        print("%-32s %d files, %d rows -> %s (%d rows, %d duplicates dropped)" % (
            partition, count, rows_in, name, rows_out, rows_in - rows_out))

    if not args.dry_run:
        print("compacted %d partition(s)" % merged)
    return 0


if __name__ == "__main__":
    sys.exit(main())
