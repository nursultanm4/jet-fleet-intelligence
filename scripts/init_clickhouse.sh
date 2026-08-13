# Wrapper for ClickHouse initialization (Docker / Linux)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "${SCRIPT_DIR}/init_clickhouse.py"