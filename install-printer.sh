#!/usr/bin/env bash
# Configure one local CUPS queue. Never downloads or executes vendor packages.
set -euo pipefail
export LC_ALL=C LC_MESSAGES=C

VERSION='1.0.1'

usage() {
    cat <<'HELP'
CUPS Printer Installer
Usage:
  bash install-printer.sh --name NAME --uri URI --driverless [OPTIONS]
  bash install-printer.sh --name NAME --uri URI --ppd FILE [OPTIONS]

Required:
  --name NAME       Queue name: letters, digits, underscores and hyphens (1-127).
  --uri URI         ipp://, ipps://, socket:// or lpd:// URI, without credentials.
  --driverless      Use IPP Everywhere (requires an ipp:// or ipps:// printer).
  --ppd FILE        Use a trusted, uncompressed local PPD instead.

Options:
  --description TEXT  Human-readable printer description.
  --location TEXT     Printer location.
  --dry-run           Validate and display the command; do not contact CUPS.
  --update            Allow updating an existing queue (not a backup/rollback).
  -h, --help          Display this help.
  --version           Display version.

Without --dry-run this command modifies local CUPS and enables the named queue.
It does not set the default printer, share the queue or print a test page.
HELP
}

die() {
    printf 'Error: %s\n' "$1" >&2
    exit "${2:-2}"
}

value_required() {
    [[ $# -ge 2 && -n $2 && $2 != --* ]] || die "Missing value for $1."
}

name='' uri='' ppd='' description='' location=''
driverless=false dry_run=false update=false
while (($#)); do
    case "$1" in
        --name) value_required "$@"; name=$2; shift 2 ;;
        --uri) value_required "$@"; uri=$2; shift 2 ;;
        --ppd) value_required "$@"; ppd=$2; shift 2 ;;
        --description) value_required "$@"; description=$2; shift 2 ;;
        --location) value_required "$@"; location=$2; shift 2 ;;
        --driverless) driverless=true; shift ;;
        --dry-run) dry_run=true; shift ;;
        --update) update=true; shift ;;
        -h|--help) usage; exit 0 ;;
        --version) printf '%s\n' "$VERSION"; exit 0 ;;
        *) die "Unknown option: $1. Use --help." ;;
    esac
done

[[ $(uname -s) == Linux ]] || die 'This installer supports Linux only.'
[[ $name =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,126}$ ]] || die 'Invalid or missing queue name.'
uri_pattern='^(ipp|ipps|socket|lpd)://(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9][A-Za-z0-9.-]*)(:[0-9]+)?(/[^[:space:][:cntrl:]]*)?$'
[[ $uri =~ $uri_pattern ]] || die 'Invalid or missing printer URI.'
[[ $uri != *'@'* && $uri != *'?'* && $uri != *'#'* && $uri != *'\'* ]] || die 'Credentials, query strings and fragments are not supported in URIs.'
for text in "$description" "$location"; do
    [[ ! $text =~ [[:cntrl:]] ]] || die 'Description and location must not contain control characters.'
done

command=(lpadmin -h localhost -p "$name" -E -v "$uri")
if $driverless; then
    [[ -z $ppd ]] || die 'Choose either --driverless or --ppd, not both.'
    [[ $uri == ipp://* || $uri == ipps://* ]] || die 'IPP Everywhere requires an ipp:// or ipps:// URI.'
    command+=(-m everywhere)
else
    [[ -n $ppd ]] || die 'Choose --driverless or provide --ppd FILE.'
    [[ -f $ppd && -r $ppd ]] || die 'PPD must be a readable local file.'
    IFS= read -r first_line < "$ppd" || [[ -n ${first_line:-} ]] || die 'PPD is empty.'
    [[ $first_line == '*PPD-Adobe:'* ]] || die 'File does not begin with a PPD-Adobe header; extract compressed drivers first.'
    # Resolve relative paths before passing them to CUPS; paths may contain spaces.
    ppd_dir=$(cd -- "$(dirname -- "$ppd")" && pwd -P)
    ppd="$ppd_dir/$(basename -- "$ppd")"
    command+=(-P "$ppd")
fi
[[ -z $description ]] || command+=(-D "$description")
[[ -z $location ]] || command+=(-L "$location")
command+=(-o printer-is-shared=false)

if $dry_run; then
    printf 'Dry run: local CUPS will not be contacted. Queue state and device compatibility are not checked.\n'
    printf 'Command: '
    printf '%q ' "${command[@]}"
    printf '\n'
    exit 0
fi

for tool in lpadmin lpstat; do
    command -v "$tool" >/dev/null 2>&1 || die "Required CUPS command not found: $tool." 3
done
# lpstat -r can exit successfully even when CUPS is stopped. Check its status
# text as well; LC_MESSAGES is explicit because CUPS can prefer it to LC_ALL.
scheduler_status=$(lpstat -h localhost -r 2>/dev/null) || die 'Local CUPS scheduler is unavailable.' 3
[[ $scheduler_status == 'scheduler is running' ]] || die 'Local CUPS scheduler is unavailable or its status could not be confirmed.' 3
queues=$(lpstat -h localhost -p 2>/dev/null) || die 'Unable to inspect existing queues; no changes made.' 3
exists=false
while read -r kind queue rest; do
    if [[ $kind == printer && ${queue,,} == "${name,,}" ]]; then
        exists=true
        break
    fi
done <<< "$queues"
if $exists && ! $update; then
    die "Queue '$name' already exists. Inspect it first; use --update to modify it explicitly." 4
fi

printf 'Configuring local CUPS queue: %s\n' "$name"
if ! "${command[@]}"; then
    die 'CUPS rejected the configuration. Inspect lpstat and the CUPS logs; a partial configuration may remain.' 5
fi
lpstat -h localhost -p "$name" >/dev/null 2>&1 || die 'Configuration submitted, but queue verification failed. Inspect local CUPS.' 5
printf "Queue '%s' configured and enabled. No test job was sent.\n" "$name"
