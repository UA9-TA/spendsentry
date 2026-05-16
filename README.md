# SpendSentry

[![CI](https://github.com/UA9-TA/spendsentry/actions/workflows/ci.yml/badge.svg)](https://github.com/UA9-TA/spendsentry/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/spendsentry.svg)](https://badge.fury.io/py/spendsentry)

*The $34,000 bug existed for 8 days. SpendSentry would have caught it in 12 minutes.*

## The incident
A developer recently pushed code containing a runaway while loop generating unlimited API requests, unnoticed until they received a $34,000 bill from their cloud provider 8 days later. Cloud platforms alert you when you cross billing thresholds—often after the damage is done.

**SpendSentry watches spend velocity per deployment.** It connects directly to your cloud, matches spend acceleration to git commits, and alerts you the moment spend spikes relative to its usual rate.

## Demo
<!-- Add demo.gif here -->

## Install
```bash
pip install spendsentry
```

## Quick start
```bash
# Configure cloud provider + alert channel
spendsentry config --provider aws --alert telegram

# Start the daemon (monitors spend continuously)
spendsentry daemon start

# Set spend limits
spendsentry limit --daily 50 --hourly 5 --alert-at 80
```

## Sample output
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

## How it works
1. **Polls Cost API**: Background daemon queries cloud cost (AWS Cost Explorer) every 5 minutes.
2. **Calculates Velocity**: Checks current rate against historical 7-day average for the same time.
3. **Correlates**: If a spike (>2.5x normal) is found, maps it to the nearest preceding git commit.
4. **Alerts**: Immediately fires a notification to Telegram, Slack, or Email.

## Supported providers
- AWS ✅
- GCP 🔜
- Azure 🔜

## Alert channels
- Telegram ✅
- Slack ✅
- Email 🔜

## CI integration
Run a one-shot check as a deployment gate.
```bash
spendsentry check --fail-if-over 10
```

## Configuration reference
Configuration is stored in `~/.spendsentry/config.toml`. Use the CLI `spendsentry config` and `spendsentry limit` to manage settings.

## Contributing / License
MIT License. Contributions welcome!

---

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
