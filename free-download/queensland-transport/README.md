# Queensland Real-Time Transportation

[Translink](https://translink.com.au/) is the source for Queensland transportation data.




```
pip install gtfs-realtime-bindings pyarrow
./translink_parquet.py --once                     # snapshot, 5 official regions
./translink_parquet.py --all --once                # snapshot, all 18 known regions
./translink_parquet.py --mode Bus --interval 20 --max-runtime 86400
./translink_parquet.py --summary        # optional: pip install duckdb
```

## Regions

Translink [officially documents](https://translink.com.au/about-translink/open-data/gtfs-rt)
5 realtime region codes; these are polled by default:

| Code | Region |
|---|---|
| `SEQ` | South East Queensland |
| `CNS` | Cairns |
| `NSI` | North Stradbroke Island |
| `MHB` | Maryborough-Hervey Bay |
| `BOW` | Bowen |

The [static GTFS schedule dataset](https://www.data.qld.gov.au/dataset/general-transit-feed-specification-gtfs-translink)
lists 19 regional service areas in total, one per named resource. Cross-checking
the other 14 names against the realtime API turned up working, undocumented
codes for all but one of them — pass `--all` to poll these too, or `--region
<code>` to poll a single one:

| Code | Region |
|---|---|
| `BUN` | Bundaberg |
| `GLT` | Gladstone |
| `GYM` | Gympie |
| `INN` | Innisfail |
| `KIL` | Kilcoy |
| `MKY` | Mackay |
| `MAG` | Magnetic Island |
| `MAL` | Maleny-Landsborough |
| `RKY` | Rockhampton-Yeppoon |
| `TWB` | Toowoomba |
| `TSV` | Townsville |
| `WAR` | Warwick |
| `WHT` | Whitsundays |

No working realtime code was found for **Magnetic Island Ferry** — it may be
folded into `MAG`, or have no separate GTFS-RT feed.

## Trip lines

`route_lines.py` exports clean per-trip GeoJSON lines from the Parquet
dataset, splitting each trip wherever the gap between fixes is too large to
be real travel (e.g. a vehicle idling at the depot, pre-tagged with its next
trip_id) instead of drawing one spurious line straight across the map:

```
pip install duckdb
./route_lines.py 608 --out route608.geojson              # by route prefix
./route_lines.py 608-5021 --exact --out route608-A.geojson  # exact route_id
```

## Example: --summary output

```
./translink_parquet.py --summary | column -t -s$'\t'
trip_id                    route     vehicle                                pts  first_fix            last_fix             mins   km      max_gap_m
37602366-WBS 26_27-42911   529-4841  9F10C7088E8F64E70D53AB5059107979_71    15   2026-08-12 05:57:29  2026-08-12 07:24:16  86.8   72.903  17205.0
38144199-LVB 26_27-43541   539-5020  3369089D8AB8CC897DFFEE57B7433815_47    125  2026-08-11 18:14:34  2026-08-11 19:43:22  88.8   61.398  6497.0
37546296-KBL 26_27-42862   649-4889  5D96518F670F165D25D65701F847ABD1_31    125  2026-08-11 18:14:13  2026-08-11 19:36:19  82.1   59.723  10032.0
38144214-LVB 26_27-43541   539-5020  3369089D8AB8CC897DFFEE57B7433815_47    36   2026-08-12 10:05:56  2026-08-12 11:51:33  105.6  59.697  14427.0
37611545-PRT 26_27-42922   540-4827  F6A5E87C8208E2E9E469ED3B2A6BB3B7_13    16   2026-08-12 07:40:18  2026-08-12 09:34:37  114.3  59.145  13187.0
37602325-WBS 26_27-42910   529-4841  9F10C7088E8F64E70D53AB5059107979_71    99   2026-08-11 18:43:09  2026-08-11 19:49:18  66.2   55.806  7677.0
37546280-KBL 26_27-42862   649-4889  5D96518F670F165D25D65701F847ABD1_60    13   2026-08-12 08:37:00  2026-08-12 09:50:23  73.4   54.671  16733.0
38337660-TDEV 26_27-43722  281-4867  DE58B3C0DF18AF7D25F833371D98199B_227   17   2026-08-12 05:57:31  2026-08-12 07:56:53  119.4  54.266  10584.0
38155601-LCBS 26_27-43547  563-4985  06EAC06E55F06AEC6418AEEBA19D5764_51    176  2026-08-12 13:23:02  2026-08-12 15:02:13  99.2   53.066  2520.0
38157548-SUN 26_27-43550   631-5021  E3AF327034B532B7BE0ED4C555A486FE_5797  184  2026-08-12 12:06:48  2026-08-12 13:35:56  89.1   52.706  1283.0
38156746-SUN 26_27-43550   630-5021  E3AF327034B532B7BE0ED4C555A486FE_5758  144  2026-08-12 13:45:28  2026-08-12 15:10:24  84.9   52.324  7684.0
37586716-SBL 26_27-42893   743-4843  73DD7B678B530932DF783319BBF95E95_756   14   2026-08-12 07:54:35  2026-08-12 09:16:30  81.9   51.494  20788.0
37546274-KBL 26_27-42862   649-4889  5D96518F670F165D25D65701F847ABD1_11    20   2026-08-12 07:06:35  2026-08-12 08:21:08  74.6   51.472  14875.0
38158380-SUN 26_27-43550   631-5021  E3AF327034B532B7BE0ED4C555A486FE_5642  153  2026-08-12 11:20:02  2026-08-12 13:07:30  107.5  49.644  4631.0
37546281-KBL 26_27-42862   649-4889  5D96518F670F165D25D65701F847ABD1_60    14   2026-08-12 10:06:01  2026-08-12 11:20:18  74.3   49.05   18459.0
38157376-SUN 26_27-43550   622-5021  E3AF327034B532B7BE0ED4C555A486FE_5716  193  2026-08-12 11:12:55  2026-08-12 13:43:05  150.2  48.973  782.0
37611527-PRT 26_27-42922   540-4827  F6A5E87C8208E2E9E469ED3B2A6BB3B7_17    119  2026-08-12 13:39:12  2026-08-12 14:53:19  74.1   48.278  3935.0
38158477-SUN 26_27-43550   622-5021  E3AF327034B532B7BE0ED4C555A486FE_5634  179  2026-08-12 12:13:57  2026-08-12 13:36:33  82.6   48.162  791.0
38341254-BT 26_27-43727    330-4948  A7393ED51E387246BB3D6249943091E8_2152  199  2026-08-12 12:54:28  2026-08-12 15:07:46  133.3  47.995  6388.0
38144216-LVB 26_27-43541   539-5020  3369089D8AB8CC897DFFEE57B7433815_47    106  2026-08-12 13:00:52  2026-08-12 13:54:22  53.5   47.674  1464.0
```
