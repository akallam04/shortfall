#!/bin/sh
set -eu

expected_repo="https://github.com/akallam04/oversold.git"

fail() {
	echo "setup-oversold: $*" >&2
	exit 1
}

root=$(git rev-parse --show-toplevel) || fail "not inside a git repository"
lock="$root/oversold.lock"
dest="$root/.oversold"

[ -f "$lock" ] || fail "missing $lock"
repo=$(sed -n 's/^repo=//p' "$lock")
commit=$(sed -n 's/^commit=//p' "$lock")

[ "$repo" = "$expected_repo" ] || fail "oversold.lock repo must be $expected_repo, got '$repo'"
printf '%s' "$commit" | grep -Eq '^[0-9a-f]{40}$' || fail "oversold.lock commit must be 40 lowercase hex characters, got '$commit'"

if [ -e "$dest" ]; then
	chmod -R u+w "$dest"
	rm -rf "$dest"
fi

git clone --quiet "$repo" "$dest"
git -C "$dest" -c advice.detachedHead=false checkout --quiet --detach "$commit"

head=$(git -C "$dest" rev-parse HEAD)
[ "$head" = "$commit" ] || fail "HEAD is $head, expected $commit"
[ -z "$(git -C "$dest" status --porcelain)" ] || fail "clone is not clean after checkout"

[ -f "$dest/.env.example" ] || fail "missing .oversold/.env.example"
umask 077
awk '
BEGIN { srand() }
/^POSTGRES_PORT=/ { print "POSTGRES_PORT=55433"; seen["POSTGRES_PORT"] = 1; next }
/^MEDUSA_PORT=/ { print "MEDUSA_PORT=9010"; seen["MEDUSA_PORT"] = 1; next }
/^MEDUSA_2_PORT=/ { print "MEDUSA_2_PORT=9011"; seen["MEDUSA_2_PORT"] = 1; next }
/^COMPOSE_PROJECT_NAME=/ { next }
{
	line = $0
	while (index(line, "change-me") > 0) {
		cmd = "openssl rand -hex 32"
		cmd | getline secret
		close(cmd)
		i = index(line, "change-me")
		line = substr(line, 1, i - 1) secret substr(line, i + 9)
	}
	print line
}
END {
	if (!seen["POSTGRES_PORT"]) print "POSTGRES_PORT=55433"
	if (!seen["MEDUSA_PORT"]) print "MEDUSA_PORT=9010"
	if (!seen["MEDUSA_2_PORT"]) print "MEDUSA_2_PORT=9011"
	print "COMPOSE_PROJECT_NAME=shortfall-oversold"
}
' "$dest/.env.example" > "$dest/.env"
chmod 600 "$dest/.env"
umask 022
if grep -q 'change-me' "$dest/.env"; then
	fail ".env still contains change-me"
fi

(cd "$dest" && make build && make test)

binary="$dest/bin/oversold"
[ -x "$binary" ] || fail "missing $binary after make build"

count=0
for f in "$dest"/scenarios/medusa/*; do
	[ -f "$f" ] || continue
	(cd "$dest" && ./bin/oversold validate "$f")
	count=$((count + 1))
done
[ "$count" -gt 0 ] || fail "no scenarios found in .oversold/scenarios/medusa"

if command -v docker >/dev/null 2>&1; then
	first=$(cd "$dest" && env -u COMPOSE_PROJECT_NAME docker compose config | head -n 1)
	[ "$first" = "name: shortfall-oversold" ] || fail "docker compose config first line is '$first'"
	echo "docker compose config: $first"
fi

[ -z "$(git -C "$dest" status --porcelain)" ] || fail "clone is not clean after build and test"
chmod -R a-w "$dest"

echo "oversold commit: $head"
echo "oversold binary: $binary"
echo "scenarios validated: $count"
