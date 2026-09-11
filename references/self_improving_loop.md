# Reference: Nujin's Autonomous Self-Improving Quant Loop & Meta-Tool Evolution

## 1. Overview: The Self-Improving Quant Paradigm

Traditional quantitative development is bottlenecked by human manual trial-and-error: running a couple of backtests, eyeballing equity curves, and abandoning experiments without logging failure causes.

**Nujin's Self-Improving Engine** automates quantitative alpha discovery into an unbroken, disk-grounded optimization loop:
1. **Source of Truth on Disk:** All state, baseline metrics, rule hypotheses, failure patterns, and run logs live on disk in `.nujin/` (or `.autoresearch/`). The agent never relies on ephemeral conversational memory.
2. **Strict Binary Scoring:** Every cycle evaluates candidate strategies against unambiguous **yes/no** programmatic checks (`tools/vectorized_screener.py` and `tools/validation_cynic.py`).
3. **Fixed Regime Validation Set (Apples-to-Apples):** Progress is measured exclusively by performance on fixed historical market slices (Bull trend expansion, Bear liquidation cascade, Ranging consolidation).
4. **Confidence Margin Decision:** A candidate rule is promoted to `best_rules.json` **only** if its validation score strictly beats the reigning champion by a confidence margin ($\ge 1$). Otherwise, it is discarded and reverted.
5. **Plateau Breakers:** If 5 consecutive cycles yield no improvement, Nujin resets and synthesizes an orthogonal hypothesis from accumulated failure patterns.
6. **Meta-Tool Evolution:** Nujin does not merely optimize trading rules—it audits, benchmarks, and evolves its own CLI tools, expands reference manuals, and refactors computational bottlenecks over time.

---

## 2. The 5-Phase Self-Improving Architecture

```
[ Phase 1: Market & Codebase Discovery ]
  Scan candles, existing features, active strategies, server and cockpit status.
                    │
                    ▼
[ Phase 2: Target & Hypothesis Selection ]
  User-defined goal OR systematic scan across 6 quant quality dimensions.
                    │
                    ▼
[ Phase 3: Binary Metric Definition ]
  Formulate 4-6 strict yes/no criteria (Sharpe >= 1.8, MaxDD <= 4.5%, DSR >= 0.95).
                    │
                    ▼
[ Phase 4: Disk Setup & Baseline (.nujin/) ]
  Initialize state.json, rules.json, validation_slices, results.jsonl.
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               PHASE 5: CONTINUOUS AUTONOMOUS LOOP                      │
│                                                                        │
│   1. Load state from disk (.nujin/state.json, results.jsonl)           │
│   2. Sample slices (fixed validation set + rotating regime chunks)     │
│   3. Formulate / Mutate candidate rules using structured operators      │
│   4. Execute isolated evaluations (tools/vectorized_screener.py)       │
│   5. Compute binary validation score (0 to 6)                          │
│   6. Decision:                                                         │
│        IF validation_score > best by margin -> KEEP (promote rules)    │
│        ELSE -> DISCARD (revert to best, increment plateau_counter)     │
│   7. Append full run record to .nujin/results.jsonl                    │
│   8. Dispatch UI telemetry (UPSERT_WIDGET) to Cockpit                  │
│   9. Plateau Breaker Check (if plateau_counter >= 5)                   │
│  10. Continue autonomously without stopping or asking permission       │
└────────────────────────────────────────────────────────────────────────┘
                    │ (When Goal Met)
                    ▼
[ Phase 6: Code Generation & Cockpit Deployment ]
  Emit strategies/*.py, register in StrategyManager, launch bot & signals.
```

---

## 3. Disk-Based State Machine (`.nujin/`)

The persistence contract ensures complete reproducibility:

```
.nujin/ (or .autoresearch/)
├── state.json              # Live run counter, best validation score, plateau counter
├── rules.json              # Current active candidate rule set
├── best_rules.json         # Current reigning champion rule set
└── results.jsonl           # Append-only audit history of every research cycle
```

### `state.json` Schema
```json
{
  "target": "Prop Firm Dual Wick Rejection",
  "scope": "BTC/USDT 15m / XAUUSD 1m",
  "context": "Net Sharpe >= 1.8, MaxDD <= 4.5%, DSR >= 0.95",
  "run_number": 8,
  "best_score": 6,
  "best_validation_score": 5,
  "max_score": 6,
  "confidence_margin": 1,
  "plateau_counter": 0,
  "active_mutation_operator": "restructure_exit",
  "validation_slices": [
    {"name": "slice_1_trending", "start_pct": 0.0, "end_pct": 0.35},
    {"name": "slice_2_vol_cascade", "start_pct": 0.35, "end_pct": 0.70},
    {"name": "slice_3_ranging_chop", "start_pct": 0.70, "end_pct": 1.00}
  ]
}
```

---

## 4. Execution Workflow via CLI (`tools/autoresearch_miner.py`)

Nujin manages the entire research cycle via direct CLI calls:

1. **Initialize Research State:**
   ```bash
   python tools/autoresearch_miner.py init --target "Prop Firm Dual Wick Rejection" --scope "BTC/USDT 15m"
   ```

2. **Run Single Research Step:**
   ```bash
   python tools/autoresearch_miner.py step
   ```

3. **Run Batch of Autonomous Cycles:**
   ```bash
   python tools/autoresearch_miner.py run --cycles 10
   ```

4. **Inspect Research Status & History:**
   ```bash
   python tools/autoresearch_miner.py status
   ```

---

## 5. Meta-Self-Improvement: Tool Evolution & Auditing

In addition to discovering trading strategies, Nujin actively audits and evolves its own tools:

### Automated Tool Self-Audit
```bash
python tools/autoresearch_miner.py improve-tool --tool <tool_name.py>
```
**Audit Checks:**
- **Syntax Compilation:** Compiles script via `py_compile` to verify syntax validity.
- **Shebang & Prefix:** Verifies `#!/usr/bin/env python3` and standard `TOOL_NAME = "[ToolPrefix]"`.
- **Flat Argparse Standard:** Verifies flat `action` with choices rather than fragile subparsers.
- **Latency Benchmark:** Measures CLI `--help` invocation latency in milliseconds.

### Tool Refactoring Protocols
- **Loop Vectorization:** If a tool contains slow iterative Python loops over candlestick rows, refactor to vector operations (`numpy` / `polars`).
- **Feature Additions:** When new microstructure proxies are discovered (e.g. fractional differentiation, session delta), add feature generators to `tools/feature_miner.py` and document them in `references/feature_engineering.md`.
- **Documentation Refinement:** Document verified negative results and empirical failure patterns so future mining cycles never repeat discredited hypotheses.
