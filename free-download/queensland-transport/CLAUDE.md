# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Polls Translink's GTFS-Realtime `VehiclePositions` feed (Queensland public transport — bus/rail/tram/ferry) and accumulates each vehicle's GPS fixes into a trajectory dataset. Repeated polling of the same `(vehicle_id, trip_id)` traces the path a vehicle takes from origin to destination, which downstream `--summary` queries turn into per-trip distance/duration stats.

Feed docs: https://translink.com.au/about-translink/open-data/gtfs-rt — data is CC-BY, State of Queensland, no authentication required.

## Three parallel collector scripts

The same fetch → parse → store logic is implemented three times, once per storage backend. They are independent files with **no shared modules** — a fix to `fetch()`, `parse_feed()`, `haversine()`, `feed_url()`, or the CLI args must be applied to each script individually, and it's worth checking whether it applies to one, two, or all three.

- **`translink_parquet.py`** — writes Hive-partitioned Parquet under `positions/dt=<date>/region=<region>/`, queryable directly by DuckDB without loading into a database. Buffers rows and flushes per-partition-date atomically (temp file + `os.replace`), so a reader scanning the directory never sees a half-written file. Requires `gtfs-realtime-bindings` + `pyarrow`.

## Commands

```
pip install gtfs-realtime-bindings pyarrow   # parquet variant
```

Single snapshot:
```
./translink_parquet.py --once
```

Continuous polling (e.g. all SEQ buses for a day):
```
./translink_parquet.py --mode Bus --interval 20 --max-runtime 86400
```
`--mode` is only valid with `--region SEQ` (mode-specific feeds aren't published for other regions). `--interval` below 5s is rejected as impolite to the upstream feed.

Per-trip trajectory stats (distance travelled, duration, largest gap between fixes) from already-collected data:
```
./translink_parquet.py --summary        # needs duckdb installed
```

Query the Parquet dataset directly with DuckDB, no Python involved:
```
duckdb -c "SELECT * FROM read_parquet('positions/**/*.parquet', hive_partitioning = true) LIMIT 10"
```
`cadence.sql` is a worked example (poll-interval distribution via `lag()`/`epoch()` over the partitioned dataset).

There is no test suite, linter, or build step in this directory — verification is done by running a script and inspecting `--summary` output or querying the data directly.

## Data model

One row = one timestamped GPS fix for one vehicle on one trip: `vehicle_id, ts, vehicle_label, trip_id, route_id, mode, direction_id, start_date, start_time, lat, lon, bearing, speed, odometer, stop_id, current_status, occupancy_status, congestion_level, feed_ts, fetched_at`.

- Regions: `SEQ` (South East Queensland, default), `CNS`, `NSI`, `MHB`, `BOW`.
- Feeds are polled politely via ETag/`If-None-Match`; a 304 response means no new data and is not treated as an error.
- A vehicle-reported timestamp of 0 falls back to the feed header timestamp, then to fetch time, so `ts` is never null.
- Protobuf enum fields (`current_status`, `occupancy_status`, `congestion_level`) are converted to their symbolic names via `enum_name()`, tolerating unknown values from the upstream feed.
- `mode` is not part of the GTFS-RT payload — Translink has no such field on `VehiclePosition`. It's stamped from whatever `--mode` a given `translink_parquet.py` run was collecting with, so it's `NULL` for any row collected without `--mode` (the default multi-region run). A `mode` filter downstream (`viewer_parquet.py`, `current_positions.py --mode`) only matches rows collected with that exact `--mode`, not all vehicles of that type.

## Non-code files

`translink.db`, `nohup.out`, `1`, and `positions/` are output artifacts from prior polling runs (checked in as example data), not source — don't treat them as code to maintain.
