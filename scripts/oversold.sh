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

real_root=$(cd "$root" && pwd -P)

absolute() {
	p=$1
	tail=""
	while [ ! -e "$p" ]; do
		base=$(basename "$p")
		case "$base" in
		. | ..)
			fail "cannot resolve $1"
			;;
		esac
		tail="/$base$tail"
		parent=$(dirname "$p")
		[ "$parent" != "$p" ] || fail "cannot resolve $1"
		p=$parent
	done
	if [ -d "$p" ]; then
		dir=$(cd "$p" && pwd -P)
		echo "$dir$tail"
	else
		[ -z "$tail" ] || fail "$1: $p is not a folder"
		dir=$(cd "$(dirname "$p")" && pwd -P)
		echo "$dir/$(basename "$p")"
	fi
}

inside_repo() {
	case "$1" in
	"$real_root" | "$real_root"/*) ;;
	*)
		fail "$2 resolves to $1, outside the repo"
		;;
	esac
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
	if [ "$i" -gt 1 ]; then
		if [ -e "$a" ] || { [ "$sub" = "export" ] && [ "$i" -eq "$n" ]; }; then
			abs=$(absolute "$a") || exit 2
			inside_repo "$abs" "$a"
			a=$abs
		fi
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
