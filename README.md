# agent-to-prod

**Deploy an LLM agent to production on Kubernetes in ~15 minutes — hardened by default.**

Most "deploy your agent" guides stop at `docker run`. This kit gives you the part
that actually matters in production: a non-root, minimal container, a locked-down
Kubernetes deployment, and a CI/CD pipeline that tests, scans, and ships it — so
your agent goes out the way a security-conscious platform team would ship it, not
the way a demo does.

Clone it, point it at your LLM key, and you have a real deployment. Swap the one
`call_llm()` function for your provider and the rest is done.

---

## What you get

- **A working agent service** (`app/`) — FastAPI, `/invoke`, `/healthz`,
  `/readyz`, structured logs, and a zero-setup stub so it runs with no API key.
- **A hardened image** (`Dockerfile`) — multi-stage, slim, **non-root**, no build
  tooling in the final layer. 0 hadolint issues.
- **Locked-down Kubernetes manifests** (`deploy/base/`) — non-root,
  read-only root FS, all capabilities dropped, seccomp, resource limits, probes,
  a default-deny **NetworkPolicy**, a **PodDisruptionBudget**, and anti-affinity.
- **A CI/CD pipeline** (`.github/workflows/ci.yml`) — test → build → **Trivy
  scan (fails on HIGH/CRITICAL)** → push to GHCR.
- **A `Makefile`** that gets you from clone to running in a handful of commands.

## Security posture (verified)

Rendered manifests, scanned with real tools:

| Scanner | Result |
| --- | --- |
| hadolint (Dockerfile) | **0 issues** |
| kube-score | **0 warnings**, 1 critical* |
| checkov (CIS Kubernetes) | **87 passed**, 3 failed* |

<sub>*The remaining findings are all "pin the image to a digest / don't use
`:latest`" and "secrets as files vs env" — expected for a **template** whose image
reference you replace. The included pipeline pushes a digest-pinned image, which
resolves the image-tag findings automatically. Re-check anytime with
`kustomize build deploy/base | kube-score score -` and `checkov -f`.</sub>

## The 15-minute path

```bash
# 1. run it locally — no API key needed (uses a stub)
make run           # serves on :8080
curl localhost:8080/healthz
curl -X POST localhost:8080/invoke -d '{"prompt":"hello"}' -H 'content-type: application/json'

# 2. wire your provider: edit the call_llm() function in app/main.py
#    and add your SDK to app/requirements.txt

# 3. ship it
make build                       # hardened image
make secret LLM_API_KEY=sk-...   # create the k8s secret
make deploy                      # apply the hardened manifests + wait for rollout
```

Or let the pipeline do build/scan/push on every commit — just set the repo's
packages permission and push to `main`.

## Customizing

- **Provider:** replace the body of `call_llm()` in `app/main.py`. The example
  wiring for Anthropic is in the comments.
- **Model / replicas / limits:** edit `deploy/base/deployment.yaml`.
- **Who can call the agent:** the NetworkPolicy allows pods labelled
  `role: agent-client`. Change that selector to fit your mesh/ingress.

## Why it's built this way

Every default here maps to a real production failure mode — root containers,
unbounded pods, flat networks, unscanned images. The point of the kit is that you
get the hardened version for free, instead of discovering each gap in an incident
or a security review later.

---

Built by [Abhichandra](https://www.abhichandra.online) — SRE / Platform Engineer.
If you want this wired to your stack (your provider, mesh, registry, and a full
GitOps rollout), I take that on as scoped work.

MIT licensed — use it freely.
