#!/bin/sh
set -eu

profile="shortfall"
vm_name="colima-shortfall"
socket="$HOME/.colima/$profile/docker.sock"

fail() {
	echo "engine: $*" >&2
	exit 1
}

usage() {
	echo "usage: sh scripts/engine.sh up|down|status" >&2
	exit 2
}

root=$(git rev-parse --show-toplevel) || fail "not inside a git repository"
command -v colima >/dev/null 2>&1 || fail "colima is not installed"

memory_gib() {
	bytes=$(sysctl -n hw.memsize 2>/dev/null || awk '/^MemTotal:/ { print $2 * 1024 }' /proc/meminfo)
	if [ "$bytes" -lt 17179869184 ]; then
		echo 4
	else
		echo 6
	fi
}

engine_name() {
	env -u DOCKER_CONTEXT DOCKER_HOST="unix://$socket" docker info --format '{{.Name}}' 2>/dev/null
}

check_engine() {
	[ -S "$socket" ] || fail "socket $socket is missing"
	name=$(engine_name) || fail "docker info did not answer through $socket"
	[ "$name" = "$vm_name" ] || fail "docker info through $socket reports '$name', expected '$vm_name'"
	echo "engine: docker info through $socket reports $name"
}

cmd=${1:-}
case "$cmd" in
up)
	activate=""
	saved_context=""
	if colima start --help 2>&1 | grep -q -- '--activate'; then
		activate="--activate=false"
	else
		saved_context=$(docker context show)
	fi
	set -- --profile "$profile" \
		--cpus 4 \
		--memory "$(memory_gib)" \
		--disk 40 \
		--vm-type vz \
		--mount-type virtiofs \
		--mount "$root"
	if [ -n "$activate" ]; then
		set -- "$@" "$activate"
	fi
	status=0
	colima start "$@" || status=$?
	if [ -n "$saved_context" ]; then
		docker context use "$saved_context" >/dev/null
	fi
	[ "$status" -eq 0 ] || fail "colima start failed with exit code $status"
	check_engine
	;;
down)
	colima stop --profile "$profile"
	;;
status)
	colima status --profile "$profile" 2>&1 || true
	if [ -S "$socket" ] && name=$(engine_name); then
		echo "engine: docker info through $socket reports $name"
	else
		echo "engine: no answer through $socket"
	fi
	;;
*)
	usage
	;;
esac
