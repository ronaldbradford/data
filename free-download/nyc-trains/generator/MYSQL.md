# Local MySQL for nyc_trains

A docker-compose-based MySQL, for loading `generator.py --sql` output
into somewhere queryable instead of just piping GeoJSON to a file. Not
part of `viewer.py`'s deployment (see `../viewer/deploy/DEPLOY-ubuntu.md`
for that) — this is a local/dev sink for the generator.

**Quick path**: `../test/e2e-test.sh start` does everything below in one
step (container up, wait for healthy, generator.py --sql running in the
background against it) — `../test/e2e-test.sh test` then validates it
end to end (container healthy, table exists, has rows, JSON valid), and
`../test/e2e-test.sh stop`/`clean` tears it back down; `sql` drops you
into an interactive `mysql` shell against it. Run `../test/e2e-test.sh`
with no arguments for the full command list. The rest of this doc is the
same steps done by hand, for when you want to see or adjust each one.

## 1. Load the connection info

```
direnv allow      # if you use direnv — loads .envrc automatically from here on
# or, without direnv:
source .envrc
```

`.envrc` defines `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`,
`MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` — throwaway local
values, safe to keep checked in (see the file's own header comment).
`docker-compose.yml` reads these from the environment; skip this step
and `docker compose up` refuses to start with a clear error naming the
missing variable, rather than silently starting with different
credentials than the ones you'd try to connect with.

## 2. Start MySQL

```
docker compose up -d
docker compose logs -f mysql
```

On first boot (fresh data volume) you'll see `01-schema.sql` then
`02-tables.sql` run automatically — watch for `Creating 'nyc_trains'
schema` and `Creating nyc_trains tables` in the log, then `mysqld: ready
for connections`. Subsequent starts skip both files (MySQL only runs
`docker-entrypoint-initdb.d` against an empty data directory) — see
`docker-compose.yml`'s header comment for how to force a redo.

## 3. Generate SQL and load it into the container

`generator.py --sql` emits one `INSERT` statement per line (see its own
`-h` for the full flag list). Two ways to get it into the container:

**Catch generator output to a file, then load that file** (the
straightforward two-step version — useful when you want to inspect or
reuse the file before loading it):

```
./generator.py --sql > trains.sql
docker compose exec -T mysql \
  mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < trains.sql
```

`-T` disables `exec`'s pseudo-TTY allocation, which is what lets `<
trains.sql` actually pipe in over stdin instead of fighting a terminal.

**Or pipe it straight through, no intermediate file:**

```
./generator.py --sql | docker compose exec -T mysql \
  mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"
```

Either way, `generator.py`'s own progress/error logging still goes to
stderr (see its `-h`), so it prints to your terminal even while stdout is
being redirected or piped into `mysql`.

If you have a local `mysql` client (not just the one inside the
container), `docker compose` also published the port, so this works too:

```
./generator.py --sql | mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
  -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"
```

## 4. Check what landed

```
docker compose exec mysql mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
  --default-character-set=utf8mb4 \
  -e "SELECT id, generated_at, line, train_count FROM nyc_trains ORDER BY id DESC LIMIT 10;"
```

`--default-character-set=utf8mb4` matters here — without it the client
mis-renders non-ASCII characters already present in the data (e.g. the
em dash in PATH's route names) even though they're stored correctly; see
`generator.py`'s `sql_escape()` docstring for the related (and
non-obvious) MySQL string-escaping issue that took real testing to find.

## 5. Keep it running unattended

`generator.py -n/-i` already does its own polling loop (`-n` count,
`-i` seconds between snapshots — see its `-h`; there's no unbounded
"forever" mode, so pick a large `-n` for a long-running job). Combine
with the piped form above and `nohup`/a systemd unit/whatever you use
for long-running jobs, e.g. roughly a day at 20s intervals:

```
nohup ./generator.py --sql -n 4320 -i 20 --log-file generator.log \
  2>/dev/null | docker compose exec -T mysql \
  mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" &
```

## Cleaning up

```
docker compose down       # stop, keep the data volume
docker compose down -v    # stop and delete all stored data
```
