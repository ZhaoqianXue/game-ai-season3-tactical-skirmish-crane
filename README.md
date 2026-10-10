# Season 3: The Army — Screen and Strike

## Design goal

Make the three unit types visibly complement each other: footmen form an adjacent screen, archers fight at range from advantageous ground, and cavalry seek charging opportunities against vulnerable targets. Each unit has independent memory; contact reports coordinate pursuit without shared variables.

**Rating question (1–5):** How clearly did the footmen, archers, and cavalry perform complementary roles while navigating terrain?

## Design reflection and Season 2 revisions

Season 2 peers reported weak coordination and footmen looping across water. This version replaces geometric pursuit with terrain-cost distance maps for both visible enemies and reported contacts. Legal paths remain the authority on movement. Adjacent footmen receive a small preference for shield-wall formation, archers prefer roughly five-tile engagement distance and avoid nearby melee units, and cavalry prefer enemy archers and charge-length attacks when available. Hills and forest are evaluated separately because one is terrain and the other is a feature.

Messages are sent to visible living allies every two rounds, validated by sender, and expire after three rounds. Incoming reports affect the next activation, not the action already chosen. Units without contact initially approach separate central lanes and later advance beyond the center to avoid permanent waiting.

The result is a lightweight heuristic, not a global commander. It can still split the army or follow a stale contact, and winning against the Naive baseline does not establish effectiveness against classmates. A future revision could add explicit formation slots and coordinated target assignment. The main lesson from development was to check the actual observation contract: forest/marsh are features, and hill increases vision and damage but not attack range.

## Verification

Official Season 3 settings are saved in `season.json`: army, field extent 12, terrain and unit abilities enabled. Protected `sandbox/`, manifest, and dependency files are unchanged.

- `python -m sandbox test`: 117 passed.
- `python -m sandbox eval --seeds 0 1 2 3 4` (Red vs Naive): 80.00, 77.97, 85.31, 85.62, 85.62; mean **82.91**.
- `python -m sandbox eval --seat 1 --seeds 0 1 2 3 4` (Blue vs Naive): 83.12, 82.03, 82.50, 82.34, 80.94; mean **82.19**.
- Untouched fresh-template Red baseline on the same settings/seeds: mean **25.12**. Scores are local results, not official leaderboard results.

## AI-use disclosure and reflection

OpenAI Codex was used substantially: it inspected the assignment and Season 2 feedback, designed the heuristics, wrote `agent.py`, drafted this README, ran tests and evaluations, and assisted with publication/submission. This is not a claim of unaided student implementation or of personally watching every test. No LLM/API calls run inside the submitted agent.

Checks included reading official helper implementations, exercising the actual Season 3 configuration on both sides and five seeds, and confirming that protected template files were unchanged. AI assistance accelerated implementation, but its first draft incorrectly conflated terrain and features and assumed hills extended attack range. Those errors were corrected against the supplied environment rules before the reported final evaluations. Automated scores and tests are useful evidence, but do not replace gameplay inspection or peer feedback.

## Original template usage

Edit `agent.py` to build one unit's behavior for Skirmish at Crane Reach. Every unit on a side runs a separate instance of the same `Agent` class, so they do not share state or variables. `sandbox/` is provided code: do not edit it.

Start with the [Getting Started guide](https://vox-deorum.github.io/game-sandbox/students/getting-started/). Then run these commands from this folder as you work:

```console
python -m sandbox play   # command a side yourself in your browser
python -m sandbox watch  # watch your agent take on Naive
python -m sandbox test   # run the provided checks
python -m sandbox eval   # compare your agent with Naive
```

**Naive** is a simple built-in opponent. It holds the other side in `watch` and `eval`, and `eval` reports your side's average score over repeatable matches. The [`environment.md`](environment.md) guide explains rivals, presets, and the other command options.

## Files you will use

| Path | Purpose |
| --- | --- |
| `agent.py` | Your `Agent` implementation and the first TODO locations. |
| `environment.md` | Crane rules, starter walkthrough, helpers, observations, and settings. |
| `manifest.json` | Names the agent class for a submission. |
| `season.json` | Optional local season settings downloaded from My Submissions. |
| `tests/` | Checks your submission should pass. |
| `sandbox/` | Local game, commands, helper package, and observation types. Do not edit it. |
| `requirements.txt` | Exact Python package versions used by the server. |
| `requirements-dev.txt` | Test dependencies. |
| `.env.example` | Example local LLM settings. |

The starter returns Crane orders with `action.move()` and `action.stay()` from `sandbox.crane`. Its `act(observation)` receives the current observation and action mask. Before changing the strategy, read [`environment.md`](environment.md). It starts with a small archer improvement you can copy, then explains when an order is legal.

Leave `sandbox/`, `requirements.in`, and `requirements.txt` unchanged. The pinned packages match the server. Ask your instructor before adding a package.

When your agent is ready, follow the shared [submitting guide](https://vox-deorum.github.io/game-sandbox/students/submitting/). For the optional `learn` and `chat` hooks, see the shared [agent interface](https://vox-deorum.github.io/game-sandbox/students/agent-interface/). Crane messaging begins in Season 3.

## Optional LLM API

If your instructor enables model calls, follow [Using the LLM API](llm.md). Copy `.env.example` to `.env`, add the endpoint and key, and never commit either secret.

Test the connection with:

```console
python -m sandbox llm
```
