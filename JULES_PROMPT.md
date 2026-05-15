# Jules Build Prompt — SpendSentry v1.0

## What You Are Building

**SpendSentry** is an open-source CLI tool that monitors cloud spend in real time and blocks deployments before costs spiral out of control. It correlates spend velocity with git commits so developers know exactly which deployment caused a cost spike — before they get the bill.

The core problem: AI coding assistants generate code with infinite loops, missing pagination, runexpected recursion, and unbounded API calls. A single AI-generated bug sent one developer's Cloudflare bill to $34,000 in 8 days. Cloud providers send billing alerts — but only after the damage. SpendSentry watches spend velocity per deployment, enforces thresholds, and fires alerts (Telegram, Slack, email) the moment spend accelerates beyond normal.

**Target:** Top GitHub trending. Every developer with a cloud bill has felt this fear.

---

## Core User Flow

```bash
# Install
pip install spendsentry

# Configure cloud provider + alert channel
spendsentry config --provider aws --alert telegram

# Start the daemon (monitors spend continuously)
spendsentry daemon start

# Check current spend velocity
spendsentry status

# See spend per deployment (correlated with git commits)
spendsentry history

# Set spend limits
spendsentry limit --daily 50 --hourly 5 --alert-at 80

# One-shot check (for CI/CD gates)
spendsentry check --fail-if-over 10   # exit 1 if today's spend > $10
```

**Output (`spendsentry status`):**
```
SpendSentry — Spend Monitor
──────────────────────────────────────────────────
✦ Today's spend       $4.21  (limit: $50.00)
✦ Last hour           $1.83  ⚠ HIGH — 3× normal rate
✦ Spend velocity      ↑ accelerating since 14:32

  Recent deployments:
  14:31  abc1234  feat: add image processor         $0.02 → $1.83/hr ← SPIKE
  11:20  def5678  fix: update dependencies          $0.18/hr (normal)
  09:05  ghi9012  chore: bump versions              $0.21/hr (normal)

✦ Alert sent          Telegram @ 14:34
✦ Recommendation      Roll back abc1234 or investigate image processor
──────────────────────────────────────────────────
```

---

## Tech Stack

- **Language:** Python 3.10+
- **CLI framework:** Typer + Rich
- **Cloud APIs:**
  - AWS: `boto3` (Cost Explorer API)
  - GCP: `google-cloud-billing` (optional, v1)
- **Alerting:** `httpx` for Telegram bot API + Slack webhooks
- **Daemon:** `schedule` library for polling loop, runs as background process
- **Git integration:** `subprocess` + `git log` for commit correlation
- **Storage:** SQLite (local) for spend history and deployment log
- **Packaging:** `pyproject.toml` (hatchling), entry point `spendsentry`
- **Config:** `~/.spendsentry/config.toml`

---

## Project Structure

```
spendsentry/
├── spendsentry/
│   ├── __init__.py
│   ├── cli.py              # Typer app — daemon, status, history, config, limit, check
│   ├── daemon.py           # Background polling loop (runs every 5 min)
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract SpendProvider base class
│   │   └── aws.py          # AWS Cost Explorer implementation
│   ├── correlator.py       # Matches spend spikes to git commits by timestamp
│   ├── alerter.py          # Sends Telegram / Slack / email alerts
│   ├── storage.py          # SQLite: stores spend snapshots + deployment log
│   ├── velocity.py         # Calculates spend velocity and detects acceleration
│   ├── display.py          # Rich terminal output
│   └── config.py           # Config file reader/writer
├── tests/
│   ├── test_velocity.py
│   ├── test_correlator.py
│   ├── test_storage.py
│   ├── test_alerter.py
│   └── fixtures/
│       ├── sample_spend_history.json   # 7 days of mock AWS Cost Explorer responses
│       └── sample_git_log.txt          # Corresponding git log with timestamps
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
└── README.md
```

---

## Detailed Module Specs

### `cli.py`
```python
app = typer.Typer(name="spendsentry", help="Real-time cloud spend monitoring and deployment guardrails")

@app.command()
def daemon(action: str):  # start | stop | restart | status
    """Manage the background spend monitoring daemon."""

@app.command()
def status():
    """Show current spend velocity and recent deployment correlation."""

@app.command()
def history(days: int = 7):
    """Show spend history with per-deployment breakdown."""

@app.command()
def limit(daily: float = None, hourly: float = None, alert_at: int = 80):
    """Set spend limits and alert thresholds."""

@app.command()
def check(fail_if_over: float = None):
    """One-shot CI check. Exit 1 if spend exceeds threshold."""

@app.command()
def config(provider: str = None, alert: str = None):
    """Configure cloud provider and alert channel."""
```

### `providers/aws.py` — AWS Cost Explorer
- Use `boto3.client("ce")` with `get_cost_and_usage()`
- Granularity: `HOURLY` for real-time velocity
- Metrics: `UnblendedCost`
- Group by: `SERVICE` for per-service breakdown
- Credentials: reads from standard AWS env vars / `~/.aws/credentials`
- Cache responses for 5 minutes to avoid API rate limits

### `velocity.py` — Spend velocity calculation
```python
@dataclass
class VelocityReport:
    current_hourly_rate: float
    baseline_hourly_rate: float     # 7-day average same time of day
    acceleration_factor: float      # current / baseline
    is_spiking: bool                # acceleration_factor > 2.5
    spike_started_at: datetime
```
Spike detection: if current hour rate > 2.5× the 7-day average for that hour-of-day → spike.

### `correlator.py` — Git commit correlation
- Read `git log --format="%H %ai %s" -n 20`
- For each spend snapshot in storage, find the most recent git commit before the spike started
- Return `{commit_hash, message, author, timestamp}` as the probable cause

### `alerter.py` — Multi-channel alerts
- **Telegram:** `POST https://api.telegram.org/bot{token}/sendMessage`
- **Slack:** POST to webhook URL
- Alert message: current rate, limit, probable commit, recommended action
- Rate-limit alerts: max 1 alert per 30 minutes for the same spike

### `storage.py` — SQLite persistence
Two tables:
- `spend_snapshots`: `(id, timestamp, hourly_cost, daily_cost, provider, raw_json)`
- `deployment_log`: `(id, commit_hash, message, timestamp, spend_at_deploy, peak_spend)`

---

## README Spec

1. **Hero** — badges + one-liner: *"The $34,000 bug existed for 8 days. SpendSentry would have caught it in 12 minutes."*
2. **The incident** — reference the real Cloudflare DOs infinite loop story (paraphrased)
3. **Demo** — `<!-- Add demo.gif here -->`
4. **Install** — `pip install spendsentry`
5. **Quick start** — configure AWS, start daemon, set limit
6. **Sample output** — exact Rich status output from above
7. **How it works** — 4-step: poll Cost Explorer → calculate velocity → correlate with git → alert
8. **Supported providers** — AWS ✅, GCP 🔜, Azure 🔜
9. **Alert channels** — Telegram ✅, Slack ✅, email 🔜
10. **CI integration** — `spendsentry check --fail-if-over 10` in GitHub Actions
11. **Configuration reference** — all config options
12. **Contributing / License**

---

## `pyproject.toml`

```toml
[project]
name = "spendsentry"
version = "0.1.0"
description = "Real-time cloud spend monitoring that catches runaway costs before you get the bill"
authors = [{name = "UA9-TA", email = "vkrmsatsangi@gmail.com"}]
keywords = ["cloud", "aws", "cost", "monitoring", "developer-tools", "cli", "devops"]
dependencies = [
    "typer>=0.12", "rich>=13", "boto3>=1.34",
    "httpx>=0.27", "schedule>=1.2",
    "tomli>=2.0; python_version < '3.11'",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "pytest-mock", "pytest-cov", "moto>=5.0"]

[project.scripts]
spendsentry = "spendsentry.cli:app"

[project.urls]
Homepage = "https://github.com/UA9-TA/spendsentry"
Changelog = "https://github.com/UA9-TA/spendsentry/blob/main/CHANGELOG.md"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--ignore=tests/fixtures"

[tool.ruff]
line-length = 100
target-version = "py310"
[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]
```

Use `moto` to mock AWS Cost Explorer in tests — no real AWS credentials needed in CI.

---

## Fixtures

### `tests/fixtures/sample_spend_history.json`
7 days of mock AWS Cost Explorer hourly responses (JSON matching the real API shape). Include a clear spike on day 5 matching a specific commit timestamp.

### `tests/fixtures/sample_git_log.txt`
`git log` output with 10 commits over 7 days. The commit timestamped just before the spike should be `feat: add image processor` (the culprit).

---

## CI

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "${{ matrix.python-version }}"}
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --cov=spendsentry --cov-fail-under=40
      - run: ruff check spendsentry/
      - run: ruff format --check spendsentry/
```

---

## Definition of Done

- [ ] `spendsentry daemon start` runs polling loop in background
- [ ] `spendsentry status` shows velocity from fixture data
- [ ] `spendsentry history` shows deployment correlation from fixtures
- [ ] `spendsentry check --fail-if-over 10` exits 1 correctly
- [ ] Telegram alert sends (with mock token in tests)
- [ ] Spike detection correctly flags the fixture spike
- [ ] Git correlator identifies the right commit from fixture log
- [ ] CI passes on Python 3.10, 3.11, 3.12
- [ ] ruff passes


## The Developer Toolkit Ecosystem

This tool is part of a suite of open-source AI-powered developer tools built by the same team:

| Tool | What it does |
|---|---|
| **[RootCause](https://github.com/UA9-TA/rootcause)** | Auto-diagnose failing tests — AI root cause + fix |
| **[ErrorMentor](https://github.com/UA9-TA/errormentor)** | Auto-diagnose production errors — correlate logs with git commits |
| **[TestGap](https://github.com/UA9-TA/testgap)** | Find untested code paths after every commit |
| **[HalluCheck](https://github.com/UA9-TA/hallucheck)** | Catch AI hallucinations in code diffs |
| **[IntentDiff](https://github.com/UA9-TA/intentdiff)** | Understand what a diff *actually* does semantically |
| **[DepSecure](https://github.com/UA9-TA/depsecure)** | Block vulnerable dependencies at commit time |
| **[ArchGuard](https://github.com/UA9-TA/archguard)** | Enforce microservice architecture rules across repos |
| **[SpendSentry](https://github.com/UA9-TA/spendsentry)** | Monitor cloud spend in real time — alert before costs spiral |
| **[ContextKit](https://github.com/UA9-TA/contextkit)** | Build minimal AI context bundles — 88% fewer tokens |

## Repo Details
- GitHub: https://github.com/UA9-TA/spendsentry
- Local path: /Users/chitra/Documents/Projects/spendsentry
- Branch: main — License: MIT
