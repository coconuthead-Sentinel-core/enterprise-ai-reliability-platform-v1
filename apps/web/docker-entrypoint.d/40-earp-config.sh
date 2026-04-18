#!/bin/sh
set -eu

cat > /usr/share/nginx/html/config.js <<EOF
window.__EARP_CONFIG__ = {
  apiBase: "${API_BASE_URL:-}"
};
EOF
