#!/usr/bin/env bash

################################################################################
# run_locally.sh - Create an oarepo release locally and run the integration tests
#
# This script automates the complete workflow for invenio packages,
# running all commands in the correct order with sensible defaults.
#
# Usage: ./run_locally.sh [OPTIONS]
#
# Options:
#   --skip-step STEP    Skip the specified step (can be used multiple times)
#   --start-with STEP   Start execution from the specified step (1-4)
#   --help, -h          Show this help message
#
# Steps:
#   1. setup-venv       Create and setup Python virtual environment
#   2. initialization   Setup integration tests and clone repositories
#   3. run-tests        Run tests for all packages
#   4. upload-original  Upload original packages to CESNET registry
#   5. update-entrypoints Update entrypoints in patched packages
#   6. find-distributions Find distributions for patched packages
#   7. build-distributions Build source and wheel distributions for modified packages
#   8. upload-distributions Upload distributions to CESNET registry
#   9. update-oarepo    Update oarepo package version and dependencies
#
# Examples:
#   ./run_locally.sh                    # Run all steps
#   ./run_locally.sh --skip-step 3      # Skip running tests
#   ./run_locally.sh --start-with 2     # Start from initialization step
#   ./run_locally.sh --skip-step 1 --skip-step 3  # Skip venv setup and tests
#

# Function to show usage
usage() {
    sed -n '2,/^$/p' "$0" | sed 's/^##*//'
    exit 0
}

set -e
set -o pipefail
set -u

cd "$(dirname "$0")"

# Default options
SKIP_STEPS=()
START_WITH=""
DEV_RELEASE=f
# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-step)
      SKIP_STEPS+=("$2")
      shift 2
      ;;
    --start-with)
      START_WITH="$2"
      shift 2
      ;;
    --dev-release)
      usage
      ;;
    *)
      echo "Error: Unknown option: $1"
      echo ""
      usage
      ;;
  esac
done

# Function: Step 1 - Setup virtual environment
step_1() {
  echo "=== Step 1: Setup virtual environment ==="
  
  if [ -d .venv ]; then
    rm -rf .venv
  fi
  
  uv venv --python=3.14
  source .venv/bin/activate
  uv pip install -e .
  
  echo "✓ Step 1 complete"
}

# Function: Step 2 - Initialization
step_2() {
  echo "=== Step 2: Initialization ==="
  
  if [ -d workdir ]; then
    rm -rf workdir
  fi

  # Setup the integration tests
  invenio-integration-tests setup invenio-forks.yaml test.json

  # create an array of --patch arguments for each patch in test.json
  patches=()
  while IFS= read -r patch; do
    patches+=(--patch "$patch")
  done < <(jq -r '.patches[]' test.json)

  # initialize the workdir and clone all repositories
  invenio-testrig setup --verbose  --repository oarepo/inveniordm-reference-repo \
    --patch-mode pinned-rebase  --test-mode stop-on-success --debug \
    "${patches[@]}"
  
  echo "✓ Step 2 complete"
}

# Function: Step 3 - Run tests
step_3() {
  echo "=== Step 3: Run tests ==="
  
  # run tests for all the packages. It will take significant time to run all the tests!
  invenio-testrig test --all
  
  echo "✓ Step 3 complete"
}

# Function: Step 4 - Upload original packages
step_4() {
  echo "=== Step 4: Upload original packages to CESNET registry ==="
  
  # upload original packages to the CESNET package registry (pip needs a single source
  # of truth for the package registry, so if we patch/have patched a package, all the other
  # versions of the package also need to be uploaded to the CESNET registry, 
  # otherwise pip will not be able to find them)
  invenio-integration-tests upload-original workdir
  
  echo "✓ Step 4 complete"
}

step_5() {
  echo "=== Step 5: Update entrypoints in patched packages ==="
  
  # update entrypoints in patched packages based on configuration
  invenio-integration-tests update-entrypoints workdir
  
  echo "✓ Step 5 complete"
}

step_6() {
  echo "=== Step 6: Find distributions for patched packages ==="
  
  # find existing distributions for patched packages and check if they match
  invenio-integration-tests find-distributions workdir
  9
  echo "✓ Step 6 complete"
}

step_7() {
  echo "=== Step 7: Build source and wheel distributions for modified packages ==="
  
  # create source and wheel distributions for all modified packages 
  invenio-integration-tests build-distributions workdir
  
  echo "✓ Step 7 complete"
}

step_8() {
  echo "=== Step 8: Upload distributions to CESNET registry ==="
  
  # upload the built distributions to CESNET GitLab PyPI registry
  invenio-integration-tests upload-distributions workdir
  
  echo "✓ Step 8 complete"
}

step_9() {
  echo "=== Step 9: Update oarepo package ==="
  
  # update the oarepo package version and dependencies
  # version propagation is now automatic based on app-rdm version
  invenio-integration-tests update-oarepo workdir
  
  echo "✓ Step 9 complete"
}

# ===========================
# Step execution logic
# ===========================

STEPS=()
LAST_STEP=9
# generate a sequence of 1 ... LAST_STEP or START_WITH ... LAST_STEP
if [[ -n "$START_WITH" ]]; then
  for i in $(seq "$START_WITH" "$LAST_STEP"); do
    STEPS+=("$i")
  done
else
  for i in $(seq 1 "$LAST_STEP"); do
    STEPS+=("$i")
  done
fi

FILTERED_STEPS=()
for step in "${STEPS[@]}"; do
  if [[ ! " ${SKIP_STEPS[*]} " =~ " $step " ]]; then
    FILTERED_STEPS+=("$step")
  fi
done

# now run through the filtered steps and execute the corresponding functions
for step in "${FILTERED_STEPS[@]}"; do
  step_$step
done

echo ""
echo "=== All steps completed successfully ==="



