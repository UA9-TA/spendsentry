# SpendSentry
**The $34,000 bug existed for 8 days. SpendSentry would have caught it in 12 minutes.**

SpendSentry is an open-source CLI tool that monitors cloud spend in real time and blocks deployments before costs spiral out of control. It correlates spend velocity with git commits so developers know exactly which deployment caused a cost spike — before they get the bill.

## The Incident
A single AI-generated bug with an infinite loop and missing pagination sent a developer's bill to $34,000 in 8 days. Cloud providers send billing alerts — but only after the damage is done. SpendSentry watches spend velocity per deployment, enforces thresholds, and fires alerts the moment spend accelerates beyond normal.

## Demo
<!-- Add demo.gif here -->

## Install
```bash
pip install spendsentry
```

## Quick Start
```bash
# Configure cloud provider + alert channel
spendsentry config --provider aws --alert telegram

# Start the daemon (monitors spend continuously)
spendsentry daemon start

# Set spend limits
spendsentry limit --daily 50 --hourly 5 --alert-at 80
```

## Sample Output
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

## How It Works
1. Polls AWS Cost Explorer
2. Calculates spend velocity and spike detection
3. Correlates with git commits
4. Alerts on spikes

## Supported Providers
- AWS ✅
- GCP 🔜
- Azure 🔜

## Alert Channels
- Telegram ✅
- Slack ✅
- Email 🔜

## CI Integration
```bash
spendsentry check --fail-if-over 10
```

## Configuration Reference
Config file is stored at `~/.spendsentry/config.toml`.

## Contributing / License
MIT License.
