# Queensland Real-Time Transportation

[Translink](https://translink.com.au/) is the source for Queensland transportation data.




```
pip install gtfs-realtime-bindings pyarrow
./translink_parquet.py --once
./translink_parquet.py --mode Bus --interval 20 --max-runtime 86400
./translink_parquet.py --summary        # optional: pip install duckdb
