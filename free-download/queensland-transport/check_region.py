#!/usr/bin/env python
"""Check whether a Translink GTFS-Realtime region code is valid and has data.

Fetches https://gtfsrt.api.translink.com.au/api/realtime/<REGION>/VehiclePositions
and prints the feed header and vehicle entity count.

An HTTP 404 (Azure BlobNotFound) means the region code doesn't exist.
HTTP 200 with entities == 0 means the region is real but no vehicles are
currently reporting positions -- poll again later to be sure it's not just
an off-peak lull.

Requires: pip install gtfs-realtime-bindings

Example:
    ./check_region.py TWB

    Known: SEQ CNS NSI MHB BOW
    Extra: BUN GLT GYM INN KIL MKY MAG MAL RKY TWB TSV WAR WHT
"""

import argparse
import sys
import urllib.error
import urllib.request

from google.transit import gtfs_realtime_pb2

FEED_BASE = "https://gtfsrt.api.translink.com.au/api/realtime"
USER_AGENT = "translink-region-check/1.0"


def fetch(region):
    """Fetch the VehiclePositions payload for a region. Returns (url, status, payload)."""
    url = "%s/%s/VehiclePositions" % (FEED_BASE, region)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return url, response.status, response.read()


def main():
    parser = argparse.ArgumentParser(
        description="Check a Translink region code for validity and live data.")
    parser.add_argument("region", help="region code to test, e.g. SEQ, TWB")
    args = parser.parse_args()

    try:
        url, status, payload = fetch(args.region)
    except urllib.error.HTTPError as error:
        print("%s -> HTTP %d: not a valid region code" % (args.region, error.code),
              file=sys.stderr)
        print(error.read().decode("utf-8", "replace"), file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError) as error:
        print("fetch failed: %s" % error, file=sys.stderr)
        return 1

    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(payload)
    except Exception as error:
        print("%s -> HTTP %d but payload did not parse as GTFS-RT: %s" % (
            args.region, status, error), file=sys.stderr)
        return 1

    print("region:    %s" % args.region)
    print("url:       %s" % url)
    print("http:      %d" % status)
    print("gtfs_rt:   %s" % feed.header.gtfs_realtime_version)
    print("feed_ts:   %d" % feed.header.timestamp)
    print("entities:  %d" % len(feed.entity))

    if len(feed.entity) == 0:
        print("\nvalid region, but no vehicles are currently reporting "
              "(poll again later, or over time, to be sure)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
