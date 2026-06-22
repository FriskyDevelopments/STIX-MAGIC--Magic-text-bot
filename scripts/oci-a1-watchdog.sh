#!/usr/bin/env bash
# Retry Oracle Ampere (VM.Standard.A1.Flex) until pupbot-arm exists or capacity opens.
#
# Modes:
#   OCI_WATCHDOG_MODE=once   — one launch attempt (for cron / GitHub Actions); default
#   OCI_WATCHDOG_MODE=loop   — sleep and retry until success (long-running worker)
#
# Local:
#   ./scripts/oci-a1-watchdog.sh
#
# Cloud (GitHub Actions): see .github/workflows/oci-a1-watchdog.yml
#
# Loop on a always-on host (e.g. Azure ClipBunker):
#   OCI_WATCHDOG_MODE=loop OCI_RETRY_INTERVAL_SEC=900 ./scripts/oci-a1-watchdog.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OCI_REGION="${OCI_REGION:-mx-monterrey-1}"
OCI_WATCHDOG_MODE="${OCI_WATCHDOG_MODE:-once}"
OCI_RETRY_INTERVAL_SEC="${OCI_RETRY_INTERVAL_SEC:-900}"
OCI_MAX_ATTEMPTS="${OCI_MAX_ATTEMPTS:-0}"
OCI_INSTANCE_NAME="${OCI_INSTANCE_NAME:-pupbot-arm}"
OCI_SUBNET_ID="${OCI_SUBNET_ID:-ocid1.subnet.oc1.mx-monterrey-1.aaaaaaaauezvuqqgs6pzymu7wpby7n53xemhpw77bjeeqck2yhh6va3a7ltq}"
OCI_IMAGE_ID="${OCI_IMAGE_ID:-ocid1.image.oc1.mx-monterrey-1.aaaaaaaaceynxvqo6j6txzkdpwuf4jckqf73y3ui5ozihvwggsmd5sccvryq}"
OCI_A1_OCPUS="${OCI_A1_OCPUS:-1}"
OCI_A1_MEMORY_GB="${OCI_A1_MEMORY_GB:-6}"

export OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING=True

if [[ -n "${OCI_PRIVATE_KEY:-}" ]]; then
  # shellcheck source=/dev/null
  source "${SCRIPT_DIR}/oci-config-from-env.sh"
fi

TENANCY="${OCI_TENANCY_OCID:-${OCI_TENANCY:-$(grep '^tenancy=' "${OCI_CLI_CONFIG_FILE:-$HOME/.oci/config}" 2>/dev/null | head -1 | cut -d= -f2- || true)}}"
if [[ -z "${TENANCY}" ]]; then
  echo "No OCI tenancy: set OCI_TENANCY_OCID or ~/.oci/config" >&2
  exit 1
fi

_ssh_file() {
  if [[ -n "${OCI_SSH_AUTHORIZED_KEYS:-}" ]]; then
    local tmp
    tmp="$(mktemp)"
    printf '%s\n' "$OCI_SSH_AUTHORIZED_KEYS" >"$tmp"
    echo "$tmp"
    return
  fi
  local path="${OCI_SSH_PUBKEY:-${HOME}/.ssh/id_ed25519.pub}"
  if [[ ! -f "$path" ]]; then
    echo "SSH key missing: set OCI_SSH_AUTHORIZED_KEYS or OCI_SSH_PUBKEY" >&2
    exit 1
  fi
  echo "$path"
}

_find_instance_json() {
  oci search resource structured-search \
    --region "$OCI_REGION" \
    --tenant-id "$TENANCY" \
    --query-text "query Instance resources where displayName = '${OCI_INSTANCE_NAME}'" \
    --limit 5 \
    --output json 2>/dev/null || echo '{"data":{"items":[]}}'
}

_report_if_exists() {
  local payload item state ocid
  payload="$(_find_instance_json)"
  item="$(python3 -c "
import json,sys
d=json.load(sys.stdin)
items=(d.get('data') or {}).get('items') or []
print(json.dumps(items[0]) if items else '')
" <<<"$payload")"
  if [[ -z "$item" || "$item" == "null" ]]; then
    return 1
  fi
  state="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('lifecycle-state',''))" <<<"$item")"
  ocid="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('identifier',''))" <<<"$item")"
  echo "Found ${OCI_INSTANCE_NAME} | state=${state} | ocid=${ocid}"
  if [[ "$state" == "RUNNING" && -n "$ocid" ]]; then
    ip="$(oci compute instance list-vnics --region "$OCI_REGION" --instance-id "$ocid" --query 'data[0].\"public-ip\"' --raw-output 2>/dev/null || true)"
    if [[ -n "$ip" && "$ip" != "null" ]]; then
      echo "Public IP: ${ip}"
    fi
  fi
  return 0
}

_attempt_launch() {
  local ssh_tmp="" ssh_path ad
  ad="${OCI_AVAILABILITY_DOMAIN:-$(oci iam availability-domain list --compartment-id "$TENANCY" --region "$OCI_REGION" --query 'data[0].name' --raw-output)}"
  ssh_path="$(_ssh_file)"
  if [[ "$ssh_path" == /tmp/* ]]; then
    ssh_tmp="$ssh_path"
  fi

  echo "Launch attempt | region=${OCI_REGION} ad=${ad} shape=VM.Standard.A1.Flex"
  set +e
  launch_out="$(oci compute instance launch \
    --region "$OCI_REGION" \
    --compartment-id "$TENANCY" \
    --availability-domain "$ad" \
    --display-name "$OCI_INSTANCE_NAME" \
    --shape "VM.Standard.A1.Flex" \
    --shape-config "{\"ocpus\":${OCI_A1_OCPUS},\"memoryInGBs\":${OCI_A1_MEMORY_GB}}" \
    --subnet-id "$OCI_SUBNET_ID" \
    --image-id "$OCI_IMAGE_ID" \
    --assign-public-ip true \
    --ssh-authorized-keys-file "$ssh_path" \
    --wait-for-state RUNNING \
    --max-wait-seconds "${OCI_LAUNCH_MAX_WAIT_SEC:-3600}" \
    --output json 2>&1)"
  launch_rc=$?
  set -e
  [[ -n "$ssh_tmp" ]] && rm -f "$ssh_tmp"

  if [[ $launch_rc -eq 0 ]]; then
    echo "$launch_out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
data=d.get('data') or d
print('SUCCESS', data.get('id',''), data.get('lifecycle-state',''))
"
    _report_if_exists || true
    return 0
  fi

  if echo "$launch_out" | grep -qiE 'out of host capacity|OutOfHostCapacity'; then
    echo "CAPACITY: Out of host capacity in ${OCI_REGION} — will retry."
    return 2
  fi
  echo "LAUNCH_ERROR:"
  echo "$launch_out" | tail -30
  return 1
}

_run_once() {
  if _report_if_exists; then
    echo "Nothing to do — instance already present."
    exit 0
  fi
  set +e
  _attempt_launch
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    echo "OCI A1 instance is up."
    exit 0
  fi
  if [[ $rc -eq 2 ]]; then
    echo "Next attempt: cron (once mode) or sleep (loop mode)."
    exit 0
  fi
  exit 1
}

_run_loop() {
  attempt=0
  while true; do
    attempt=$((attempt + 1))
    echo "=== Watchdog attempt ${attempt} @ $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    if _report_if_exists; then
      echo "Done — instance exists."
      exit 0
    fi
    set +e
    _attempt_launch
    rc=$?
    set -e
    if [[ $rc -eq 0 ]]; then
      exit 0
    fi
    if [[ "$OCI_MAX_ATTEMPTS" -gt 0 && "$attempt" -ge "$OCI_MAX_ATTEMPTS" ]]; then
      echo "Max attempts (${OCI_MAX_ATTEMPTS}) reached."
      exit 1
    fi
    echo "Sleeping ${OCI_RETRY_INTERVAL_SEC}s before next try..."
    sleep "$OCI_RETRY_INTERVAL_SEC"
  done
}

case "$OCI_WATCHDOG_MODE" in
  once) _run_once ;;
  loop) _run_loop ;;
  *)
    echo "Unknown OCI_WATCHDOG_MODE=${OCI_WATCHDOG_MODE} (use once|loop)" >&2
    exit 1
    ;;
esac
