To get an AI agent to break out of consensus thinking—without banning the core tools it already knows—you must change **how it manipulates concepts**, not just what tools it is allowed to touch.

When you keep standard indicators on the table, an LLM naturally clusters into default associations (e.g., `RSI < 30` $\rightarrow$ oversold $\rightarrow$ buy). Out-of-the-box discovery happens when the model is forced to repurpose, invert, or context-shift those familiar tools.

---

### Core Prompt Frameworks for Lateral Innovation

**1. Functional Re-Purposing (Tool Inversion)**
Instead of using an indicator for its stated textbook purpose, force the model to interpret it through an unconventional physical or statistical lens.

* *Instruction:*
> "Take standard indicators (e.g., RSI, Bollinger Bands, ATR) and forbid their textbook interpretation. Treat them purely as signals of something else:
> * Treat oscillators as measures of **herding density / crowd positioning**, not price exhaustion.
> * Treat volatility bands as **liquidity wall probes**, not boundaries of a normal distribution.
> How does the signal change when treated as a measure of counterparty panic rather than price level?"
> 
> 



**2. Asymmetric Context Splitting (Regime Modulation)**
LLMs love applying one uniform rule across all market states. Force it to create conditional logic where the same indicator means opposite things depending on the background state.

* *Instruction:*
> "Do not create symmetrical signals (if buy on condition A, then sell on inverse condition A).
> Pair every indicator with an orthogonal metric that flips its meaning. Example: When order book liquidity is dense, a high RSI indicates momentum; when liquidity thins out, the exact same RSI indicates an exhaustion trap. Propose 3 edge cases where an indicator's textbook buy signal becomes an immediate short entry."



**3. Second-Order & Derivative Transformations**
Instead of evaluating the indicator's raw value, force the agent to look at the rate of change, acceleration, or variance of the indicator itself.

* *Instruction:*
> "Never evaluate indicator values in isolation. Compute their higher-order derivatives:
> * The velocity and acceleration of the indicator (e.g., $\Delta \text{RSI} / \Delta t$).
> * The divergence between the indicator's speed and price's speed.
> * Dynamic standard deviation or z-score of the indicator's own historical distribution over the last $N$ periods."
> 
> 



---

### Procedural Scaffolding for the Agent

To operationalize this inside an automated agent loop, structure its reasoning into a divergent-convergent pipeline rather than a single generation step.

```
Step 1: Consensus Baseline
   └─ "What is the obvious 80% consensus way to use these indicators for this setup?"

Step 2: Failure-Mode Dissection
   └─ "Under what exact market conditions does this consensus setup blow up accounts?"

Step 3: Lateral Re-combination
   └─ "Synthesize a rule that explicitly hunts that specific blow-up point using the same indicators."

```

#### Production System Prompt Add-on for Edge Mining

```markdown
### Lateral Ideation Protocol

When formulating new strategy solutions:

1. The "Crowd Liquidity" Premise:
   Assume standard retail setups (moving average bounces, classic RSI divergences) are well-known to high-frequency market makers. Instead of following the signal, analyze where the stops of retail traders cluster when that signal triggers. How can we use the standard indicator to map out trapped capital?

2. Hybrid Feature Synthesizer:
   Whenever combining two features, they must measure fundamentally different physical properties of the market:
   - Dimension A: Price Geometry / Dispersion (e.g., Bollinger, ATR)
   - Dimension B: Force & Participation (e.g., Volume, Cumulative Delta, Imbalance)
   - Dimension C: Time & Decay (e.g., Duration at price, session half-life)
   Never combine two indicators that measure the same dimension (e.g., RSI + Stochastic).

3. The "Weird Combinations" Drill:
   Propose at least one solution that intentionally pairs an indicator from macro trends with a micro tick-level trigger to create an edge based on multi-timeframe friction.

```

---

