#!/bin/sh
set -eu

profile="shortfall"
vm_name="colima-shortfall"
socket="$HOME/.colima/$profile/docker.sock"

fail() {
	echo "oversold.sh: $*" >&2
	exit 2
}

root=$(git rev-parse --show-toplevel) || fail "not inside a git repository"
dest="$root/.oversold"

commit=$(sed -n 's/^commit=//p' "$root/oversold.lock")
pin_ok=1
if [ ! -d "$dest/.git" ]; then
	pin_ok=0
elif [ "$(git -C "$dest" rev-parse HEAD 2>/dev/null)" != "$commit" ]; then
	pin_ok=0
elif [ -n "$(git -C "$dest" status --porcelain 2>/dev/null)" ]; then
	pin_ok=0
elif [ ! -x "$dest/bin/oversold" ]; then
	pin_ok=0
fi
[ "$pin_ok" -eq 1 ] || fail "the Oversold clone does not match oversold.lock or is not built, run make oversold"

absolute() {
	if [ -d "$1" ]; then
		(cd "$1" && pwd -P)
	else
		dir=$(cd "$(dirname "$1")" && pwd -P)
		echo "$dir/$(basename "$1")"
	fi
}

sub=${1:-}

n=$#
i=0
while [ "$i" -lt "$n" ]; do
	a=$1
	shift
	i=$((i + 1))
	if [ "$sub" = "run" ]; then
		case "$a" in
		-out | --out | -out=* | --out=*)
			fail "run does not accept --out, run folders always go to $root/runs"
			;;
		esac
	fi
	if [ "$i" -gt 1 ] && [ -e "$a" ]; then
		a=$(absolute "$a")
	fi
	set -- "$@" "$a"
done

unset DOCKER_CONTEXT
DOCKER_HOST="unix://$socket"
export DOCKER_HOST

check_engine() {
	[ -S "$socket" ] || fail "the shortfall engine is not running (no socket at $socket), run make engine-up"
	name=$(docker info --format '{{.Name}}' 2>/dev/null) || fail "docker info did not answer through $socket, run make engine-up"
	[ "$name" = "$vm_name" ] || fail "docker info through $socket reports '$name', expected '$vm_name', run make engine-up"
}

case "$sub" in
up | down)
	[ "$#" -eq 1 ] || fail "$sub takes no arguments"
	check_engine
	cd "$dest"
	exec make "$sub"
	;;
run)
	check_engine
	mkdir -p "$root/runs"
	set -- "$@" --out "$root/runs"
	;;
esac

cd "$dest"
exec ./bin/oversold "$@"
