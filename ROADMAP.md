# SolanaLM Roadmap

> The near-term plan for SolanaLM: what it is today, where it's going, and — most
> importantly — the cheapest credible path from a working prototype to a network the
> agent economy can actually pay for and (increasingly) verify.

For the detailed, phase-by-phase engineering plan (deliverables, timelines, team,
budget, risk register), see [`docs/roadmap.md`](docs/roadmap.md). This file is the
strategic overview and the production-viability checklist.

## Vision

SolanaLM is a hybrid decentralized AI network: OpenAI-compatible LLM inference and
federated learning, with settlement and node incentives on Solana. Operators earn SOL
by serving inference and contributing GPU cycles; developers get an inference endpoint
that swaps in for a centralized API with a base-URL change.

The 2026 bet is narrow and concrete. Two markets are converging:

- **The agent economy needs machine-payable inference.** Autonomous agents make far more
  inference calls than humans, at lower margins, and increasingly hold their own wallets.
  Per-request micropayments with sub-second finality — not monthly invoices and seat
  licenses — are the settlement model that fits. Solana gives ~400ms finality and
  ~$0.00025 fees, which is what makes per-call settlement economically real rather than
  a rounding error swallowed by gas.

- **DePIN GPU compute needs a serving layer, not just a marketplace.** Idle GPUs are
  abundant; a working, monetized, OpenAI-compatible serving stack on top of them is not.
  Generic compute marketplaces rent hardware by the hour and leave routing, billing, and
  the serving stack to the operator. SolanaLM is the opinionated serving-and-settlement
  layer for that hardware.

Where SolanaLM is heading: **on-chain, increasingly verifiable AI.** Today the chain
settles payment and anchors an audit trail. The roadmap moves progressively toward
inference that a paying agent can *verify* — attestation of which model produced a
result, on what inputs, from a node with a known reputation — so trust shifts from "the
invoice says so" to "the chain and the attestation say so."

Non-goals: we are not building a new L1, a new token standard, or a general compute
marketplace. SolanaLM is a focused protocol for paid, decentralized, OpenAI-compatible
inference and federated learning.

## Where we are (v0.1.x)

Shipped and working today:

- FastAPI gateway with JWT + Solana-signature auth, per-route rate limits, input
  sanitization, and audit logging.
- OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/completions`).
- Multi-backend inference: local PyTorch/Transformers, llama.cpp (GGUF), and proxied
  OpenAI/Anthropic/Cohere/Ollama behind one wire protocol.
- Federated learning runtime: FedAvg, FedProx, FedAdam, SCAFFOLD, with secure
  aggregation and differential privacy.
- Node registry with health checks and circuit breakers.
- Per-request SOL settlement primitives (solana-py, pynacl, base58).
- Optional 3-hop onion routing for confidential inference.
- Operations: Prometheus metrics, WebSocket admin dashboard, Redis cache,
  SQLAlchemy 2 + asyncpg, Alembic migrations, Docker Compose, Kubernetes manifests.

Honest status: this is early software. On-chain layouts, schemas, and APIs may change
between releases. Settlement and metering are functional but not yet production-hardened
(see the checklist below). Treat v0.1.x as a working reference implementation, not a
managed network.

## Milestones

### M1 — Payable inference (near term)
Make paid, metered inference production-viable end to end.
- Harden per-request settlement + metering (see "Payment settlement and metering").
- Session/escrow model for streaming completions so payment resolves against actual
  tokens served, not an up-front estimate.
- Stable, versioned OpenAI-compatible API surface with documented rate limits.
- First-class agent-wallet flow: an agent funds a session and pays per call without a
  human in the loop.

### M2 — Trustable routing (mid term)
Make it safe to route work to nodes you don't operate.
- Node reputation and quality scoring feeding the router.
- Model-availability guarantees: the registry only routes a model to nodes that can
  actually serve it, with capability attestation.
- Failure/dispute handling backed by the on-chain audit trail.

### M3 — Verifiable inference (longer term)
Move from "trust the operator" toward "verify the result."
- Inference-result attestation: signed evidence of which model + config produced a
  result (see "Inference-result verification").
- Progressive verification tiers — from lightweight signed attestation to sampled
  re-execution to (research) cryptographic proofs — so callers pick their trust/cost
  trade-off.
- Public reputation + attestation data an agent can query before it pays.

### M4 — Ecosystem (opportunistic)
- Liquid staking / delegation for node operators.
- Broader model catalog and multi-modal serving.
- Deeper Solana-DeFi composability for payouts and staking.

## Cheapest path to production

The whole point of building on Solana + DePIN is that you do **not** need a large capital
outlay to reach a working, payable network. The cheapest credible path:

### 1. Settlement on Solana (cheap by design)
Keep money movement on-chain and keep it thin.
- **Settle per request, meter in aggregate.** Do not fire one on-chain transaction per
  token. Open a funded **session/escrow** per client (or per agent wallet), meter usage
  off-chain against it, and settle on close or on a threshold. At ~$0.00025/tx, even
  frequent settlement is negligible; batching keeps it invisible.
- **Devnet → a small mainnet float.** Develop entirely on devnet (free). Go to mainnet
  with a minimal SOL float — Solana fees are sub-cent, so working capital for settlement
  is measured in dollars, not thousands.
- **No new token.** SOL-denominated payouts avoid the cost, legal exposure, and liquidity
  burden of launching and supporting a token. Add one only if a concrete mechanism (not
  fundraising) demands it.
- **Use SPL / stablecoin settlement where price stability matters.** For operators who
  want to avoid SOL volatility on earnings, settle in an SPL stablecoin over the same
  rails; the fee profile is identical.

### 2. Operators on the cheapest GPU markets
You do not buy GPUs. Operators bring them, and the cheapest inference-capable hardware
wins. Recommended, in rough order of cost-efficiency for serving open models:

- **DePIN GPU networks** — io.net, Akash, Render, Nosana. Spot GPU rentals here routinely
  undercut hyperscaler on-demand pricing by a wide margin. Because SolanaLM nodes are just
  containers that phone home to the registry, they drop straight onto this hardware.
- **Community/marketplace GPU** — Vast.ai, RunPod community/spot, TensorDock. Best raw
  $/hour for consumer and prosumer cards (RTX 4090 / 3090 / A6000-class), which serve
  quantized 7B–13B GGUF models cost-effectively.
- **Idle owned hardware.** For operators who already own GPUs, marginal cost is
  electricity; llama.cpp/GGUF backends let modest cards earn.
- **Hyperscaler spot only for burst.** AWS/GCP/Azure spot instances are the expensive tier;
  use them for elastic overflow, not baseline.

**Concrete recommendation for a first production node:** a single 24GB consumer/prosumer
GPU (RTX 4090-class) on Vast.ai/RunPod community pricing, or a DePIN spot instance on
io.net/Akash, serving a quantized 7B–8B instruct model (e.g. Llama 3.1 8B) via the
llama.cpp GGUF backend. That is a few dollars per day of hardware against per-request SOL
revenue — the smallest unit that proves the economics.

**Cheapest path, in one line:** develop on devnet, settle through funded sessions on
mainnet with a dollar-scale float, run nodes as containers on DePIN/marketplace spot GPUs,
serve quantized open models — and only add tokens, custom hardware, or heavy verification
once demand justifies the cost.

## Production-viability checklist

The gap between "runs the quickstart" and "a network strangers pay to use." Each item is
tracked toward the milestones above.

### Inference-result verification / attestation
*Status: research → M3.* Today a caller trusts that the node ran the model it claimed.
Path forward, cheapest first:
- **Signed attestation (M3, cheap):** the node signs `(model id, config hash, input hash,
  output hash, timestamp)` with its registered key; the caller and the audit log can check
  it. Catches misattribution and tampering after the fact.
- **Sampled re-execution (M3, medium):** the network re-runs a random fraction of requests
  on a second node and slashes reputation on mismatch — probabilistic honesty at low
  overhead.
- **Cryptographic proofs (research):** TEE attestation or zkML for high-assurance
  workloads. Expensive today; kept behind a tier so most traffic never pays for it.

### Payment settlement and metering
*Status: functional → hardening in M1.*
- Session/escrow so streaming completions settle against tokens actually served.
- Deterministic, auditable metering (tokens in/out, model, node) written to the audit log.
- Idempotent settlement and retry-safe payout so no double-charge / double-pay on network
  hiccups.
- Refund/dispute path anchored to on-chain records.

### Node reputation and routing
*Status: registry exists; scoring in M2.*
- Reputation from success rate, latency, correctness (from sampled re-execution), and
  uptime.
- Reputation-weighted routing with quality/latency SLAs the router enforces.
- Sybil resistance: stake or reputation cost to join meaningful routing tiers.

### Model availability
*Status: declared in config; guarantees in M2.*
- Capability attestation so the registry only advertises a model on nodes that can serve it.
- Availability targets per model and graceful fallback when a preferred node is down.
- Warm-pool / pre-load hints to bound cold-start latency.

### API stability and rate limits
*Status: works; versioning in M1.*
- Versioned, documented OpenAI-compatible surface with a deprecation policy.
- Published, enforced rate limits and quotas per key/session.
- Backpressure and fair-queueing so one heavy caller can't starve the network.

## Get involved

- Docs: <https://docs.cryptuon.com/solanalm/>
- Site: <https://solanalm.cryptuon.com/>
- Issues / discussion: <https://github.com/cryptuon/solanalm/issues>

Open an issue to discuss anything on this roadmap — especially if you want to run
verification experiments or bring DePIN GPU inventory to the network.
