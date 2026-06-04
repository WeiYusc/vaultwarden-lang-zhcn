#!/usr/bin/env bash
set -euo pipefail

IMAGE="${VAULTWARDEN_IMAGE:-vaultwarden/server:1.36.0}"
PORT="${SMOKE_PORT:-8099}"
ADMIN_TOKEN="${ADMIN_TOKEN:-vaultwarden-lang-zhcn-smoke-token}"
SMTP_SMOKE="${SMTP_SMOKE:-0}"
SMTP_SMOKE_PORT="${SMTP_SMOKE_PORT:-1025}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${SMOKE_CONTAINER_NAME:-vw-lang-zhcn-smoke-$$}"
DATA_DIR="$(mktemp -d "${TMPDIR:-/tmp}/vw-lang-zhcn-smoke.XXXXXX")"
COOKIE_JAR="$DATA_DIR/cookies.txt"
SMTP_LOG="$DATA_DIR/smtp.log"
SMTP_PID=""

cleanup() {
  set +e
  if [[ -n "$SMTP_PID" ]]; then
    kill "$SMTP_PID" >/dev/null 2>&1 || true
    wait "$SMTP_PID" >/dev/null 2>&1 || true
  fi
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf "$DATA_DIR"
}
trap cleanup EXIT

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "[FAIL] missing required command: $1" >&2; exit 1; }
}

check_tcp_port_free() {
  local port="$1"
  local label="$2"
  python3 - "$port" "$label" <<'PY'
import socket
import sys
port = int(sys.argv[1])
label = sys.argv[2]
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", port))
    except OSError as exc:
        raise SystemExit(f"[FAIL] {label} port 127.0.0.1:{port} is not available: {exc}")
PY
}

start_smtp_debug_server() {
  local port="$1"
  local log="$2"
  python3 -u - "$port" "$log" <<'PY' &
import socketserver
import sys
from pathlib import Path

port = int(sys.argv[1])
log_path = Path(sys.argv[2])

class SMTPHandler(socketserver.StreamRequestHandler):
    def send_line(self, line: str) -> None:
        self.wfile.write((line + "\r\n").encode("ascii"))
        self.wfile.flush()

    def handle(self) -> None:
        self.send_line("220 vaultwarden-lang-zhcn smoke smtp")
        data_lines = []
        in_data = False
        while True:
            raw = self.rfile.readline(1024 * 1024)
            if not raw:
                break
            line = raw.rstrip(b"\r\n")
            upper = line.upper()
            if in_data:
                if line == b".":
                    with log_path.open("ab") as fh:
                        fh.write(b"---------- MESSAGE FOLLOWS ----------\n")
                        for item in data_lines:
                            fh.write(item + b"\n")
                        fh.write(b"------------ END MESSAGE ------------\n")
                    self.send_line("250 2.0.0 OK")
                    data_lines = []
                    in_data = False
                else:
                    data_lines.append(line)
                continue
            if upper.startswith(b"EHLO") or upper.startswith(b"HELO"):
                self.send_line("250-localhost")
                self.send_line("250 HELP")
            elif upper.startswith(b"MAIL FROM:") or upper.startswith(b"RCPT TO:"):
                self.send_line("250 OK")
            elif upper == b"DATA":
                self.send_line("354 End data with <CR><LF>.<CR><LF>")
                in_data = True
            elif upper == b"RSET" or upper == b"NOOP":
                self.send_line("250 OK")
            elif upper == b"QUIT":
                self.send_line("221 Bye")
                break
            else:
                self.send_line("250 OK")

class ThreadingSMTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

log_path.write_text("[OK] SMTP debug server ready\n", encoding="utf-8")
with ThreadingSMTPServer(("127.0.0.1", port), SMTPHandler) as server:
    server.serve_forever()
PY
  SMTP_PID="$!"
  for _ in $(seq 1 30); do
    if kill -0 "$SMTP_PID" >/dev/null 2>&1 && [[ -f "$log" ]] && grep -Fq "SMTP debug server ready" "$log"; then
      echo "[OK] SMTP debug server started on 127.0.0.1:${port}"
      return 0
    fi
    sleep 0.2
  done
  echo "[FAIL] SMTP debug server did not start" >&2
  sed -n '1,80p' "$log" >&2 || true
  exit 1
}

http_get() {
  local path="$1"
  local out="$2"
  curl -fsS -b "$COOKIE_JAR" -c "$COOKIE_JAR" "http://127.0.0.1:${PORT}${path}" -o "$out"
}

assert_contains() {
  local file="$1"
  local needle="$2"
  local label="$3"
  if ! grep -Fq "$needle" "$file"; then
    echo "[FAIL] ${label}: missing marker '${needle}'" >&2
    echo "--- ${label} body excerpt ---" >&2
    sed -n '1,80p' "$file" >&2 || true
    exit 1
  fi
  echo "[OK] ${label}: contains '${needle}'"
}

assert_status_contains() {
  local path="$1"
  local marker="$2"
  local label="$3"
  local body="$DATA_DIR/${label//[^A-Za-z0-9_.-]/_}.html"
  local code
  code="$(curl -sS -b "$COOKIE_JAR" -c "$COOKIE_JAR" -o "$body" -w '%{http_code}' "http://127.0.0.1:${PORT}${path}")"
  if [[ "$code" != "200" ]]; then
    echo "[FAIL] ${label}: expected HTTP 200, got ${code}" >&2
    sed -n '1,80p' "$body" >&2 || true
    exit 1
  fi
  echo "[OK] ${label}: HTTP 200"
  assert_contains "$body" "$marker" "$label"
}

require docker
require curl
require grep
require python3

check_tcp_port_free "$PORT" "vaultwarden smoke"
if [[ "$SMTP_SMOKE" == "1" ]]; then
  check_tcp_port_free "$SMTP_SMOKE_PORT" "SMTP smoke"
fi

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[SKIP] Docker image '${IMAGE}' is not present locally; not pulling because this smoke test is offline-safe." >&2
  exit 125
fi

SMTP_ARGS=()
NETWORK_ARGS=(-p "127.0.0.1:${PORT}:80")
ROCKET_PORT_ENV=()
if [[ "$SMTP_SMOKE" == "1" ]]; then
  # Use host networking for SMTP smoke: this avoids host-gateway/firewall quirks
  # and lets the container reach the local debug server at 127.0.0.1:${SMTP_SMOKE_PORT}.
  start_smtp_debug_server "$SMTP_SMOKE_PORT" "$SMTP_LOG"
  NETWORK_ARGS=(--network host)
  ROCKET_PORT_ENV=(-e ROCKET_PORT="$PORT")
  SMTP_ARGS=(
    -e SMTP_HOST=127.0.0.1
    -e SMTP_PORT="$SMTP_SMOKE_PORT"
    -e SMTP_SECURITY=off
    -e SMTP_FROM=smoke@example.invalid
    -e SMTP_FROM_NAME="vaultwarden smoke"
  )
fi

echo "[INFO] starting ${IMAGE} as ${CONTAINER} on localhost:${PORT}"
docker run -d --name "$CONTAINER" \
  "${NETWORK_ARGS[@]}" \
  -e ADMIN_TOKEN="$ADMIN_TOKEN" \
  -e DOMAIN="http://127.0.0.1:${PORT}" \
  -e ROCKET_ADDRESS=0.0.0.0 \
  "${ROCKET_PORT_ENV[@]}" \
  -v "$ROOT_DIR/templates:/data/templates:ro" \
  -v "$DATA_DIR/data:/data" \
  "${SMTP_ARGS[@]}" \
  "$IMAGE" >/dev/null

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${PORT}/alive" >/dev/null 2>&1; then
    echo "[OK] /alive responded"
    break
  fi
  sleep 1
done
curl -fsS "http://127.0.0.1:${PORT}/alive" >/dev/null || { echo "[FAIL] /alive did not become ready" >&2; docker logs "$CONTAINER" >&2 || true; exit 1; }

login_page="$DATA_DIR/login.html"
http_get "/admin" "$login_page"
assert_contains "$login_page" "需要身份验证密钥才能继续" "/admin login"

login_code="$(curl -sS -b "$COOKIE_JAR" -c "$COOKIE_JAR" -o "$DATA_DIR/login-post.html" -w '%{http_code}' \
  -X POST --data-urlencode "token=${ADMIN_TOKEN}" "http://127.0.0.1:${PORT}/admin")"
case "$login_code" in
  200|303|302) echo "[OK] admin login POST returned HTTP ${login_code}" ;;
  *) echo "[FAIL] admin login POST returned HTTP ${login_code}" >&2; sed -n '1,80p' "$DATA_DIR/login-post.html" >&2 || true; exit 1 ;;
esac

assert_status_contains "/admin" "配置" "admin_home"
assert_status_contains "/admin/diagnostics" "诊断" "admin_diagnostics"
assert_status_contains "/admin/users/overview" "已注册的用户" "admin_users_overview"
assert_status_contains "/admin/organizations/overview" "组织" "admin_organizations_overview"

if [[ "$SMTP_SMOKE" == "1" ]]; then
  smtp_code="$(curl -sS -b "$COOKIE_JAR" -c "$COOKIE_JAR" -o "$DATA_DIR/smtp-test.out" -w '%{http_code}' \
    -H 'Content-Type: application/json' \
    -X POST --data '{"email":"smoke@example.invalid"}' \
    "http://127.0.0.1:${PORT}/admin/test/smtp")"
  if [[ "$smtp_code" != "200" ]]; then
    echo "[FAIL] SMTP smoke endpoint returned HTTP ${smtp_code}" >&2
    sed -n '1,80p' "$DATA_DIR/smtp-test.out" >&2 || true
    exit 1
  fi
  for _ in $(seq 1 20); do
    grep -Fq "Subject: Vaultwarden SMTP" "$SMTP_LOG" && break || sleep 1
  done
  assert_contains "$SMTP_LOG" "Subject: Vaultwarden SMTP" "SMTP debug output"
fi

echo "[OK] vaultwarden container smoke passed"
