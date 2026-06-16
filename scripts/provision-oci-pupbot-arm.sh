#!/usr/bin/env bash
# Provision Pupbot on Oracle Cloud Ampere (VM.Standard.A1.Flex).
# Requires: OCI CLI (~/.oci/config), SSH public key, free A1 host capacity in the AD.
#
# Usage:
#   chmod +x scripts/provision-oci-pupbot-arm.sh
#   ./scripts/provision-oci-pupbot-arm.sh
#
# If you see "Out of host capacity", use the cloud watchdog instead:
#   ./scripts/oci-a1-watchdog.sh
#   (or GitHub Actions: .github/workflows/oci-a1-watchdog.yml)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == "--watchdog" ]]; then
  exec "${SCRIPT_DIR}/oci-a1-watchdog.sh"
fi

OCI_REGION="${OCI_REGION:-mx-monterrey-1}"
export OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING=True

TENANCY="${OCI_TENANCY:-$(awk -F'= ' '/^\[DEFAULT\]/{f=1} f&&/^tenancy=/{print $2;exit}' ~/.oci/config)}"
if [[ -z "${TENANCY}" ]]; then
  echo "Set OCI_TENANCY or configure tenancy= in ~/.oci/config" >&2
  exit 1
fi

AD="${OCI_AVAILABILITY_DOMAIN:-$(oci iam availability-domain list --compartment-id "$TENANCY" --region "$OCI_REGION" --query 'data[0].name' --raw-output)}"
SUBNET="${OCI_SUBNET_ID:-ocid1.subnet.oc1.mx-monterrey-1.aaaaaaaauezvuqqgs6pzymu7wpby7n53xemhpw77bjeeqck2yhh6va3a7ltq}"
IMAGE="${OCI_IMAGE_ID:-ocid1.image.oc1.mx-monterrey-1.aaaaaaaaceynxvqo6j6txzkdpwuf4jckqf73y3ui5ozihvwggsmd5sccvryq}"
SSH_KEY="${OCI_SSH_PUBKEY:-${HOME}/.ssh/id_ed25519.pub}"
DISPLAY_NAME="${OCI_INSTANCE_NAME:-pupbot-arm}"
OCPUS="${OCI_A1_OCPUS:-1}"
MEMORY_GB="${OCI_A1_MEMORY_GB:-6}"

if [[ ! -f "$SSH_KEY" ]]; then
  echo "SSH public key not found: $SSH_KEY" >&2
  exit 1
fi

echo "Region:              $OCI_REGION"
echo "Tenancy:             ${TENANCY:0:40}..."
echo "Availability domain: $AD"
echo "Subnet:              $SUBNET"
echo "Image (Ubuntu ARM):  $IMAGE"
echo "Shape:               VM.Standard.A1.Flex (${OCPUS} OCPU, ${MEMORY_GB} GiB)"
echo "Name:                $DISPLAY_NAME"
echo

oci compute instance launch \
  --region "$OCI_REGION" \
  --compartment-id "$TENANCY" \
  --availability-domain "$AD" \
  --display-name "$DISPLAY_NAME" \
  --shape "VM.Standard.A1.Flex" \
  --shape-config "{\"ocpus\":${OCPUS},\"memoryInGBs\":${MEMORY_GB}}" \
  --subnet-id "$SUBNET" \
  --image-id "$IMAGE" \
  --assign-public-ip true \
  --ssh-authorized-keys-file "$SSH_KEY" \
  --wait-for-state RUNNING \
  --output json \
  | tee /tmp/oci-pupbot-arm-launch.json

INSTANCE_ID="$(python3 -c "import json; d=json.load(open('/tmp/oci-pupbot-arm-launch.json')); print((d.get('data') or d)['id'])")"
echo
echo "Instance OCID: $INSTANCE_ID"
echo "Public IP:"
oci compute instance list-vnics \
  --region "$OCI_REGION" \
  --instance-id "$INSTANCE_ID" \
  --query 'data[0]."public-ip"' \
  --raw-output
