#!/usr/bin/env bash
# End-to-end test/demo of the nyc-trains -> MySQL pipeline: brings up the
# docker-compose MySQL container (in ../generator), starts generator.py
# --sql running in the background piped straight into it, and can
# validate, drop you into an interactive SQL console, or tear everything
# back down on a later run. This is the actual script used to verify
# generator/docker-compose.yml + generator/01-schema.sql +
# generator/02-tables.sql + generator/generator.py --sql work together,
# not just a doc describing it.
#
# Usage:
#   ./e2e-test.sh start     # docker compose up -d, then generator.py --sql in the background
#   ./e2e-test.sh test      # validate: container healthy, table exists, has rows, JSON valid
#   ./e2e-test.sh status    # show container + background generator.py state
#   ./e2e-test.sh sql       # interactive `mysql` shell into the container
#   ./e2e-test.sh stop      # stop the background generator.py, then `docker compose down` (keeps data)
#   ./e2e-test.sh clean     # same, but `docker compose down -v` (also deletes stored data)
#
# Re-running `start` after `stop` picks up right where you left off — the
# data volume is untouched by `stop`, only `clean` wipes it. Re-running
# `start` while already running is a harmless no-op (it detects the
# already-running generator and container and leaves them be).

set -euo pipefail
# docker-compose.yml/.envrc/generator.py all live in ../generator (this
# script itself lives in test/) — run everything from there so compose's
# relative bind mounts and `./generator.py` resolve correctly regardless
# of where this script is invoked from.
cd "$(dirname "$0")/../generator"

GEN_INTERVAL="${GEN_INTERVAL:-20}"    # seconds between generator.py snapshots (its own default)
GEN_COUNT="${GEN_COUNT:-4320}"        # ~24h at the default interval — generator.py has no "forever" mode
GEN_LOG="generator.log"               # generator.py's own progress/error log (see its --log-file)
GEN_LOAD_LOG="generator-load.log"     # stdout/stderr of the `mysql` client loading generator.py's output
PID_MATCH="generator[.]py --sql"      # pgrep pattern identifying the background job (bracketed to
                                       # avoid this very script's own command line self-matching)

if [ -f .envrc ]; then
  # shellcheck disable=SC1091
  source .envrc
else
  echo "ERROR: .envrc not found here — needed for MYSQL_* connection info" >&2
  exit 1
fi

require_docker_compose() {
  docker compose version >/dev/null 2>&1 || {
    echo "ERROR: 'docker compose' not available" >&2
    exit 1
  }
}

container_healthy() {
  docker compose ps mysql 2>/dev/null | grep -q '(healthy)'
}

wait_for_mysql() {
  echo "Waiting for MySQL to report healthy..."
  for _ in $(seq 1 30); do
    container_healthy && { echo "MySQL is healthy."; return 0; }
    sleep 2
  done
  echo "ERROR: MySQL did not become healthy in time — check 'docker compose logs mysql'" >&2
  exit 1
}

start_container() {
  require_docker_compose
  echo "Starting MySQL container (docker compose up -d)..."
  docker compose up -d
  wait_for_mysql
}

stop_container() {
  require_docker_compose
  echo "Stopping MySQL container (docker compose down, data volume kept)..."
  docker compose down
}

clean_container() {
  require_docker_compose
  echo "Stopping MySQL container and deleting its data volume (docker compose down -v)..."
  docker compose down -v
}

generator_pid() {
  pgrep -f "$PID_MATCH" || true
}

start_generator() {
  local pid
  pid="$(generator_pid)"
  if [ -n "$pid" ]; then
    echo "generator.py is already running (pid $pid) — not starting a second copy."
    return 0
  fi
  echo "Starting generator.py in the background (every ${GEN_INTERVAL}s, ${GEN_COUNT} snapshots max)..."
  nohup ./generator.py --sql -n "$GEN_COUNT" -i "$GEN_INTERVAL" --log-file "$GEN_LOG" \
    2>/dev/null | docker compose exec -T mysql \
    mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
    > "$GEN_LOAD_LOG" 2>&1 &
  disown
  sleep 2
  pid="$(generator_pid)"
  if [ -n "$pid" ]; then
    echo "generator.py running (pid $pid). Logs: $GEN_LOG (generator), $GEN_LOAD_LOG (mysql load output)"
  else
    echo "ERROR: generator.py did not stay running — check $GEN_LOG / $GEN_LOAD_LOG" >&2
    exit 1
  fi
}

stop_generator() {
  local pid
  pid="$(generator_pid)"
  if [ -n "$pid" ]; then
    echo "Stopping background generator.py (pid $pid)..."
    kill "$pid" 2>/dev/null || true
    sleep 1
  else
    echo "No background generator.py running."
  fi
}

# $1: SQL, run without headers/formatting — for programmatic checks
run_query() {
  docker compose exec -T mysql mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
    --default-character-set=utf8mb4 -N -B -e "$1" 2>/dev/null
}

# $1: SQL, run with normal mysql-client formatting — for human-readable output
run_query_display() {
  docker compose exec -T mysql mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
    --default-character-set=utf8mb4 -e "$1" 2>/dev/null
}

test_pipeline() {
  require_docker_compose

  echo "== container =="
  if ! container_healthy; then
    echo "FAIL: mysql container is not healthy or not running ('$0 start' first?)" >&2
    exit 1
  fi
  echo "OK: container healthy"

  echo "== schema/table =="
  table_check="$(run_query "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${MYSQL_DATABASE}' AND table_name='nyc_trains';")"
  if [ "$table_check" != "1" ]; then
    echo "FAIL: nyc_trains table not found in schema '${MYSQL_DATABASE}' (did 01-schema.sql/02-tables.sql run? check 'docker compose logs mysql')" >&2
    exit 1
  fi
  echo "OK: nyc_trains table exists"

  echo "== data =="
  row_count="$(run_query "SELECT COUNT(*) FROM nyc_trains;")"
  echo "rows in nyc_trains: $row_count"
  if [ "$row_count" = "0" ]; then
    echo "FAIL: no rows yet — is generator.py running? ('$0 status', or '$0 start')" >&2
    exit 1
  fi

  echo "== latest row =="
  run_query_display "SELECT id, generated_at, line, train_count, JSON_VALID(position) AS json_valid FROM nyc_trains ORDER BY id DESC LIMIT 1\G"
  invalid="$(run_query "SELECT COUNT(*) FROM nyc_trains WHERE NOT JSON_VALID(position);")"
  if [ "$invalid" != "0" ]; then
    echo "FAIL: $invalid row(s) have invalid JSON in position" >&2
    exit 1
  fi
  echo "OK: all $row_count row(s) have valid JSON"

  echo
  echo "ALL CHECKS PASSED"
}

open_sql_console() {
  require_docker_compose
  if ! container_healthy; then
    echo "ERROR: mysql container is not healthy or not running ('$0 start' first?)" >&2
    exit 1
  fi
  # No -T here (unlike run_query/run_query_display): this is the one
  # place a real TTY is wanted, so `exec` allocates a pseudo-terminal and
  # you get a normal interactive `mysql>` prompt.
  docker compose exec mysql mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
    --default-character-set=utf8mb4
}

show_status() {
  echo "== container =="
  docker compose ps 2>/dev/null || true
  echo
  echo "== generator.py =="
  local pid
  pid="$(generator_pid)"
  if [ -n "$pid" ]; then
    echo "running, pid $pid"
  else
    echo "not running"
  fi
}

case "${1:-}" in
  start)
    start_container
    start_generator
    ;;
  stop)
    stop_generator
    stop_container
    ;;
  clean)
    stop_generator
    clean_container
    ;;
  test)
    test_pipeline
    ;;
  sql)
    open_sql_console
    ;;
  status)
    show_status
    ;;
  *)
    echo "Usage: $0 {start|stop|test|sql|status|clean}" >&2
    echo
    echo "  start   docker compose up -d, then generator.py --sql in the background"
    echo "  stop    stop the background generator.py, then docker compose down (keeps data)"
    echo "  test    validate: container healthy, nyc_trains table exists, has rows, JSON valid"
    echo "  sql     interactive mysql shell into the container"
    echo "  status  show container + background generator.py state"
    echo "  clean   stop everything, docker compose down -v (also deletes stored data)"
    exit 1
    ;;
esac
