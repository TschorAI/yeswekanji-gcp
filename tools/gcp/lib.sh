# Sourced by every tools/gcp/*.sh script: loads config.env, defines helpers.
# Reads: tools/gcp/config.env (or the file in $GCP_CONFIG). Writes: nothing.

set -euo pipefail
GCP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GCP_CONFIG="${GCP_CONFIG:-$GCP_DIR/config.env}"
[ -f "$GCP_CONFIG" ] || { echo "missing $GCP_CONFIG: copy config.example and fill it in" >&2; exit 1; }
# shellcheck source=/dev/null
source "$GCP_CONFIG"

step() { printf '\n== %s\n' "$*"; }
ok()   { printf '   ok: %s\n' "$*"; }
