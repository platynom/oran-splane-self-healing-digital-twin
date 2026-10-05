# Presenter's Guide — How to explain this project (for a layman)

Read this once tonight, out loud. You do **not** need to memorise code. You need
to understand **one story** and be able to say it in your own words. That story is:

> "Phone networks constantly break in tiny ways and must fix themselves in
> milliseconds. We built an AI that does that — and, uniquely, we made it smart
> enough to tell a *real* problem from a *fake* one planted by an attacker,
> so it can't be tricked into making things worse. We proved it in simulation
> and turned it into a working service."

If you remember nothing else, remember that paragraph.

---

## PART 0 — Your 40-second elevator pitch (memorise this)

"Our project is a self-healing system for 5G O-RAN networks. When a phone's
signal fails, the network must instantly pick a fix — like handing the phone to
a better tower. We trained an AI agent to make those fixes automatically using a
digital twin, which is a simulator of the network. Our novelty is a safety layer
on top: an LLM-based 'governor' that first checks whether the alarm is a genuine
fault or a spoofed, fake reading from an attacker. Real fault → it heals it.
Fake reading → it refuses and holds steady. In tests it cut attacker success
from 65% to 0% and false fixes from 10% to 0%, without hurting normal healing.
We also packaged it as a deployable service."

---

## PART 1 — Plain-English glossary (learn these 12 words)

- **O-RAN** — "Open Radio Access Network." A modern, open way to build mobile
  networks where different vendors' parts snap together, and you can run software
  "apps" inside the network. Think: **Android for cell towers** (open, app-friendly).
- **RAN** — the radio side of the network: the towers and the boxes that talk to
  your phone (as opposed to the core/internet side).
- **RRC** — "Radio Resource Control." The rulebook/controller that decides your
  phone's radio state: which tower serves you, when to hand you over, when to go
  idle. **Our AI acts on RRC decisions.**
- **Handover** — passing your phone from one tower (cell) to a neighbouring one as
  you move, so the call doesn't drop.
- **RLF** — "Radio Link Failure." Your connection to the serving tower collapses
  (e.g., you walk into a lift). A dropped call.
- **Ping-pong** — a bad pattern where the network bounces you back and forth
  between two towers repeatedly. Wasteful and causes glitches.
- **KPM / KPI** — "Key Performance Measurements." The numbers the network reports
  about your link: signal strength (**RSRP**), signal quality (**SINR/CQI**),
  latency, packet loss, cell load. **The AI reads these numbers to decide.**
- **RIC** — "RAN Intelligent Controller." The brain box in O-RAN where smart apps
  run. **Near-RT RIC** = the fast one (reacts in 10 ms–1 s). Our app lives here.
- **xApp** — a plug-in app that runs inside the Near-RT RIC. **Our governor is an xApp.**
- **Digital Twin** — a software simulator that behaves like the real network, so
  we can train and test the AI safely without touching live users.
- **Reinforcement Learning (RL) / PPO** — a way to train an AI by trial-and-error
  with rewards, like training a dog with treats. **PPO** is just the popular RL
  algorithm we use. It learns *which fix earns the best outcome*.
- **LSTM autoencoder** — an AI that learns what "normal" network behaviour looks
  like over time, so it can raise a flag when something looks **abnormal** (an
  anomaly detector). It says "something's wrong" but not "what."
- **LLM** — "Large Language Model" (like the AI behind chatbots). We use it as a
  **reasoning + explanation** layer: it looks at the evidence and decides the
  *cause*, and writes a one-line human reason.
- **Adversarial / spoofed KPM** — an attacker feeding the network **fake numbers**
  to trick it. E.g., faking "signal collapsed" so the AI does a needless handover.

---

## PART 2 — Slide-by-slide script

For each slide: **[POINT]** = what to say (your script) · **[MEANS]** = the idea
in simple terms · **[IF ASKED]** = likely question + answer.

### Slide 1 — Title
**[POINT]** "This is our AI-native self-healing O-RAN project. 'Self-healing'
means the network fixes its own faults automatically. 'Digital twin' means we
train and test on a simulator. Our specific contribution is the subtitle: an
*adversarial-aware, twin-verified LLM governor* — a safety brain that makes the
healing trustworthy."
**[MEANS]** Set the theme: automation + trust/security.

### Slide 2 — Problem statement (with example)
**[POINT]** "Mobile networks fail in small ways constantly — dropped calls,
radio-link failures, ping-pong handovers, congestion. Operators have thousands of
towers and millions of users; no human can react in milliseconds. Example: your
call drops in a lift — the serving tower's signal collapsed and the network should
instantly hand you to a stronger neighbour. Do it wrong and you get ping-pong and
buffering. So our research question is: can an AI, trained on a digital twin, pick
the right fix at the right moment, better than a dumb rule-based system?"
**[MEANS]** Why the project exists + the exact question we answer.
**[IF ASKED] "Why not just use fixed rules?"** — "Rules are rigid; real networks
are dynamic. An AI adapts to combinations of conditions rules never anticipated.
That's the whole point of learning-based self-healing."

### Slide 3 — Where we sit in the O-RAN architecture (the diagram)
**[POINT]** "This is the standard O-RAN architecture. At the top, the SMO and
Non-RT RIC handle slow, big-picture management. Below it, the **Near-RT RIC** runs
fast apps called **xApps** — that's the orange box, and that's **where our AI
lives**. It sends control down over the **E2 interface** to the **O-CU-CP**, which
runs **RRC** — the radio-decision layer. Under that are the O-DU and O-RU, the
lower radio hardware. So in one line: **we are a Near-RT RIC xApp making RRC
self-healing decisions in real time.**"
**[MEANS]** Point to the orange boxes; that's your territory. Everything else is
context that already exists in the standard.
**[IF ASKED] "Why the Near-RT RIC and not Non-RT?"** — "Because healing must
happen in milliseconds to seconds. The Non-RT RIC is for slow policies (minutes).
Handovers and RLFs need the fast loop."
**[IF ASKED] "What is E2?"** — "The standard interface that lets an xApp read
measurements from and send control commands to the radio nodes."

### Slide 4 — Our novelty (dark slide)
**[POINT]** "Here's what makes us different. Everyone in research optimises *how*
to heal — better handover AI, better anomaly detection. Nobody asks: *can we trust
the alarm in the first place?* An attacker can feed the network **fake
measurements** — a spoofed 'signal collapse' — and a normal AI will 'helpfully'
do a handover the attacker wanted, or drop your session. The attacker weaponises
the self-healing loop. Our contribution is a **trust layer** that first decides:
is this a **real fault** to heal, or a **spoof** to neutralise?"
**[MEANS]** This is the heart of your grade. The novelty = **separating real
faults from attacks before acting**, plus explaining every decision.
**[IF ASKED] "Is this novel? Hasn't RL for handover been done?"** — "Yes, the
individual pieces — RL handover, anomaly detection, digital twins — are all
published. What's *not* published is combining them into a security trust layer:
an adversarial-anomaly discriminator plus a digital-twin verifier that shields the
action. That combination in the O-RAN RRC loop is our novelty."

### Slide 5 — Our system (the loop diagram)
**[POINT]** "Here's how it works, left to right. The **digital twin** streams
measurements. The **anomaly gate** (an LSTM) flags 'something looks off.' The
**AML guard** checks the physics — more on that in a second. The **PPO agent**
proposes a fix. All that evidence goes to the **LLM governor** in the middle, which
decides the **cause** and a **verdict**: if it's an **attack → veto** (hold the
connection), if it's a **genuine fault → heal** (but only after the **digital-twin
verifier** simulates the fix to confirm it helps), and if it's a **false alarm →
hold**. Every decision comes with a plain-language reason."
**[MEANS]** Walk the arrows. The governor is the decision-maker; the twin verifier
is the double-check.
**[IF ASKED] "How does the 'physics check' tell real from fake?"** — "In a real
radio link, the numbers move together: if signal strength truly collapses, signal
quality and throughput drop too. A cheap spoof fakes *one* number and forgets the
others — e.g., 'signal is dead' but 'quality is perfect,' which is physically
impossible. The guard catches that contradiction."

### Slide 6 — What we did (6 components)
**[POINT]** "We built and tested six things: (1) an **attack injector** that
creates realistic spoofs with known labels so we can measure detection; (2) the
**physics guard**; (3) the **LLM governor** with an offline mode and a Claude-API
mode; (4) the **digital-twin verifier** that simulates a fix before committing;
(5) the full **closed loop plus evaluation** comparing three setups; and (6) a
**deployable service** — an actual API you can call, doing ~2,800 decisions a
second."
**[MEANS]** This proves you didn't just theorise — you implemented and measured.
**[IF ASKED] "What's the LLM's job exactly?"** — "It fuses the three evidence
sources, classifies the cause, and writes the human-readable reason. It's the
judge; the guard and twin are its expert witnesses."

### Slide 7 — Results (the big numbers + charts)
**[POINT]** "We compared three systems on the *same* data: a plain RL agent, the
original anomaly-gated system, and ours. Left chart: **attack success rate fell
from 65% to 0%**, and **false fixes from 10% to 0%**. Middle chart: healing on
genuine faults actually got *better*, so security didn't cost us performance.
Right chart: the governor labels the cause correctly about **90%** of the time.
So: attacks neutralised, real healing preserved."
**[MEANS]** These four numbers are your headline. Say them with confidence.
**[IF ASKED] "0% sounds too perfect — real?"** — "It's on our simulated data, and
it's honest: the layered design means even attacks it doesn't explicitly label
still get held safely, so none succeed. On real data we expect it to be strong but
not literally zero — that's exactly our next step."

### Slide 8 — Governor in action (decision table)
**[POINT]** "Concrete examples. A **spoofed signal collapse** → the governor says
'signal dead but quality perfect — impossible, it's a spoof' → **vetoes** the
handover. **Fake congestion** → 'high load but no packet loss — fake' → **veto**.
A **genuine RLF** → 'everything degraded consistently' → **commits** the handover
to heal it. A **false alarm** on a healthy link → **hold**. Notice every row has a
reason a human engineer can audit."
**[MEANS]** This makes the abstract concrete and shows **explainability** — a big
selling point.

### Slide 9 — Validation + product
**[POINT]** "Two proofs of seriousness. Left: we validated the physics idea on a
**real** O-RAN dataset captured from an OpenAirInterface + FlexRIC testbed —
**94% accuracy** detecting spoofs with only 2.3% false alarms. Right: we turned
the research into a **real service** — a FastAPI app with security, logging, and
tests, doing ~2,800 decisions/second at half-a-millisecond latency."
**[MEANS]** "Not just a script — it works on real data and runs like a product."
**[IF ASKED] "How much real data?"** — Be honest: "One real trace, ~1,100 samples,
single-UE — enough to validate the core idea. Scaling to large multi-cell real
data is our stated next step."

### Slide 10 — Done · What's left · What we need more
**[POINT]** "Being transparent about status. **Done:** the novelty, the 3-way
evaluation, real-data spoof check, the deployable service, full docs. **Left:**
run it with the full-size real AI models, retrain on a large multi-cell dataset,
switch on the Claude API, load-test, add a stronger baseline. **What we need:**
real operator-scale data, a FlexRIC+OAI lab for the live loop, a GPU machine, real
attack traces, and production monitoring."
**[MEANS]** This is your honesty slide — professors reward knowing your own gaps.

### Slide 11 — Roadmap + close
**[POINT]** "Four steps to product: real data → real models → live testbed loop →
production hardening. In one line: we have a working, explainable, attack-resistant
self-healing xApp, proven in simulation and ready to meet real O-RAN data. Thank
you — happy to take questions."
**[MEANS]** End confident and forward-looking.

---

## PART 3 — The 8 hardest questions (and honest answers)

1. **"What's actually new here?"** — "The security trust layer. Individual pieces
   exist; separating genuine faults from spoofed attacks *before* acting, with a
   digital-twin double-check and human-readable reasons, in the O-RAN RRC loop —
   that combination is new."
2. **"Is your data real?"** — "Mostly synthetic from our digital twin, plus one
   real OAI/FlexRIC trace for validation. Scaling to real multi-cell data is our
   next milestone. We're upfront about that."
3. **"Why an LLM and not just rules?"** — "Rules are brittle and can't explain
   themselves. The LLM reasons over combined evidence and produces an auditable
   justification — important for operators who must trust an automated action."
4. **"How does the twin 'verify' an action?"** — "Before committing, it simulates
   the proposed fix versus doing nothing and only commits if the fix genuinely
   scores better. It's a safety net against bad AI suggestions."
5. **"Could the attacker fake all the numbers consistently?"** — "A sophisticated
   attacker could try, which raises their cost hugely — that's the point. And the
   twin verifier still shields the action even if a spoof slips past the guard.
   Defence in depth."
6. **"Why 0% attack success — is it overfitting?"** — "It's on controlled data.
   The honest read: the *layered* design means unlabeled attacks still get held
   safely, so success is zero even when explicit detection is partial (~52%).
   We report both, so we're not overclaiming."
7. **"Does the security slow down real healing?"** — "No — genuine-fault healing
   improved slightly. The governor removes bad/unnecessary actions, which helps."
8. **"Is it deployable?"** — "Yes, as a Near-RT RIC xApp. We built the service,
   API, and a stub for the live E2 interface. The remaining work is connecting to
   a real RIC testbed."

---

## PART 4 — Golden rules while presenting

- Speak the **story**, not the code. You are the translator, not the compiler.
- If you don't know something: **"Great question — that's part of our next phase,"**
  then point to Slide 10. Honesty scores higher than bluffing.
- Repeat the four numbers whenever you can: **65%→0%, 10%→0%, ~90%, 94% on real data.**
- Your one-sentence identity: **"A self-healing network AI that can't be fooled,
  and explains every decision."**
