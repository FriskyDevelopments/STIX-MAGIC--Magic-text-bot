#!/usr/bin/env bash
# Write ~/.oci/config + API key from environment (for CI / cloud jobs).
# Required env:
#   OCI_TENANCY_OCID, OCI_USER_OCID, OCI_FINGERPRINT, OCI_REGION, OCI_PRIVATE_KEY
# Optional:
#   OCI_CONFIG_DIR (default: ~/.oci)

set -euo pipefail

: "${OCI_TENANCY_OCID:?Set OCI_TENANCY_OCID}"
: "${OCI_USER_OCID:?Set OCI_USER_OCID}"
: "${OCI_FINGERPRINT:?Set OCI_FINGERPRINT}"
: "${OCI_REGION:?Set OCI_REGION}"
: "${OCI_PRIVATE_KEY:?Set OCI_PRIVATE_KEY (PEM contents)}"

OCI_CONFIG_DIR="${OCI_CONFIG_DIR:-${HOME}/.oci}"
KEY_PATH="${OCI_CONFIG_DIR}/oci_api_key.pem"
CONFIG_PATH="${OCI_CONFIG_DIR}/config"

mkdir -p "$OCI_CONFIG_DIR"
chmod 700 "$OCI_CONFIG_DIR"
printf '%s\n' "$OCI_PRIVATE_KEY" >"$KEY_PATH"
chmod 600 "$KEY_PATH"

cat >"$CONFIG_PATH" <<EOF
[DEFAULT]
user=${OCI_USER_OCID}
fingerprint=${OCI_FINGERPRINT}
tenancy=${OCI_TENANCY_OCID}
region=${OCI_REGION}
key_file=${KEY_PATH}
EOF
chmod 600 "$CONFIG_PATH"

export OCI_CLI_CONFIG_FILE="$CONFIG_PATH"
export OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING=True
echo "OCI config written to ${CONFIG_PATH}"
