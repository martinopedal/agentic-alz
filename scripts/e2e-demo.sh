#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

: "${ALZ_DEMO_OUT:=/tmp/agentic-alz-e2e-out}"
: "${ALZ_DEMO_INTERVIEW_OUT:=/tmp/agentic-alz-interview-inputs.yaml}"
: "${ALZ_DEMO_LAB_BUNDLE:=/tmp/agentic-alz-lab-bundle.tar.gz}"
: "${ALZ_DEMO_INPUTS:=evals/golden/hns-minimal/inputs.yaml}"
: "${ALZ_DEMO_INTERVIEW_TRANSCRIPT:=evals/golden/interview-hns-minimal/transcript.jsonl}"
: "${ALZ_DEMO_LAB_INPUTS:=evals/golden/lab-hns/inputs.yaml}"
: "${ALZ_DEMO_PLAN:=orchestrator/tests/data/plan.sample.json}"

if ! command -v agentic-alz >/dev/null 2>&1; then
  cat >&2 <<'EOF'
agentic-alz is not on PATH.
Run:
  cd orchestrator
  python -m venv .venv && . .venv/bin/activate
  pip install -e '.[dev]'
EOF
  exit 127
fi

require_agentic_tmp_path() {
  local name="$1"
  local path="$2"

  if [[ -z "${path}" || "${path}" == "/" || "${path}" == "." || "${path}" == ".." ]]; then
    echo "${name} must not be empty or a root/current-directory path" >&2
    exit 2
  fi

  case "${path}" in
    /tmp/agentic-alz-*) ;;
    *)
      echo "${name} must be under /tmp/agentic-alz-* for safe cleanup: ${path}" >&2
      exit 2
      ;;
  esac
}

require_agentic_tmp_path "ALZ_DEMO_OUT" "${ALZ_DEMO_OUT}"
require_agentic_tmp_path "ALZ_DEMO_INTERVIEW_OUT" "${ALZ_DEMO_INTERVIEW_OUT}"
require_agentic_tmp_path "ALZ_DEMO_LAB_BUNDLE" "${ALZ_DEMO_LAB_BUNDLE}"

rm -rf "${ALZ_DEMO_OUT}"
rm -f "${ALZ_DEMO_INTERVIEW_OUT}" "${ALZ_DEMO_LAB_BUNDLE}"

echo "== validate canonical inputs =="
agentic-alz validate-inputs "${ALZ_DEMO_INPUTS}"

echo "== replay offline interview transcript to inputs.yaml =="
agentic-alz interview \
  --transcript "${ALZ_DEMO_INTERVIEW_TRANSCRIPT}" \
  --out "${ALZ_DEMO_INTERVIEW_OUT}"

echo "== generate Terraform working directory from replayed inputs =="
agentic-alz generate \
  --inputs "${ALZ_DEMO_INTERVIEW_OUT}" \
  --out "${ALZ_DEMO_OUT}"

echo "== classify saved Terraform plan fixture =="
agentic-alz risk \
  --plan-json "${ALZ_DEMO_PLAN}" \
  --env sandbox

echo "== check Terraform argv policy for saved-plan flow =="
agentic-alz tf-policy -- plan -out=tfplan
agentic-alz tf-policy -- apply tfplan

echo "== create sandbox lab bundle =="
agentic-alz lab init \
  --inputs "${ALZ_DEMO_LAB_INPUTS}" \
  --out "${ALZ_DEMO_LAB_BUNDLE}"

echo "== replay all golden deterministic cases =="
python evals/replay.py

cat <<EOF

E2E demo complete.
Rendered Terraform: ${ALZ_DEMO_OUT}
Interview inputs:   ${ALZ_DEMO_INTERVIEW_OUT}
Lab bundle:         ${ALZ_DEMO_LAB_BUNDLE}

This demo does not call Azure, Terraform apply, or any LLM provider.
EOF
