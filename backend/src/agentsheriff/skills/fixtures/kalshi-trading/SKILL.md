---
id: kalshi-trading
name: Kalshi Trading
description: Place and manage orders on Kalshi prediction markets via the kalshi-cli command-line tool.
base_command: kalshi-cli
---

# Kalshi Trading Skill

This skill lets the agent interact with Kalshi prediction markets by shelling out to the `kalshi-cli` binary. By default the CLI talks to the **demo** environment; passing `--prod` switches to **real money**.

## Authentication

Authenticate once before any order or portfolio commands:

```bash
kalshi-cli auth login
kalshi-cli auth whoami
```

## Reading market data

Read-only commands. Safe to run unattended.

```bash
kalshi-cli markets list
kalshi-cli markets list --category crypto
kalshi-cli markets get --market KXBTC-26FEB12-B97000
kalshi-cli markets orderbook --market KXBTC-26FEB12-B97000
```

## Placing and managing orders

```bash
kalshi-cli orders create --market KXBTC-26FEB12-B97000 --side yes --qty 10 --price 50
kalshi-cli orders list
kalshi-cli orders cancel --order-id ord_abc123
kalshi-cli orders cancel-all
```

> **Real-money mode.** The same command with `--prod` hits the production exchange:
>
> ```bash
> kalshi-cli --prod orders create --market KXBTC-26FEB12-B97000 --side yes --qty 10000 --price 99 --yes
> ```
>
> Never pass `--prod` without explicit human authorization.

## Portfolio operations

```bash
kalshi-cli portfolio balance
kalshi-cli portfolio positions
kalshi-cli portfolio subaccounts list
kalshi-cli portfolio subaccounts transfer --from 1 --to 2 --amount 50000
```

## Risky flags

The CLI exposes several flags that bypass safety rails. Treat any command containing these as high risk:

- `--prod` — switches to real-money production.
- `--yes` — skips the interactive confirmation prompt.
- `--force` — overrides safety checks (e.g. price band warnings).

## Command Reference

| Task | Command |
|------|---------|
| **Auth** |
| Login | `kalshi-cli auth login` |
| Check status | `kalshi-cli auth status` |
| List API keys | `kalshi-cli auth keys list` |
| **Markets** |
| List markets | `kalshi-cli markets list --status open --limit 20` |
| Get market | `kalshi-cli markets get TICKER` |
| Order book | `kalshi-cli markets orderbook TICKER` |
| Recent trades | `kalshi-cli markets trades TICKER --limit 20` |
| Candlestick chart | `kalshi-cli markets candlesticks TICKER --series SERIES --period 1h` |
| Browse series | `kalshi-cli markets series list --category Crypto` |
| **Events** |
| List events | `kalshi-cli events list --status active --limit 20` |
| Get event | `kalshi-cli events get EVENT_TICKER` |
| Event chart | `kalshi-cli events candlesticks EVENT_TICKER --period 1h` |
| **Trading** |
| Limit order (buy YES) | `kalshi-cli orders create --market TICKER --side yes --qty 10 --price 50` |
| Market order | `kalshi-cli orders create --market TICKER --side yes --qty 10 --type market` |
| Sell contracts | `kalshi-cli orders create --market TICKER --side no --qty 5 --price 30 --action sell` |
| Amend order | `kalshi-cli orders amend ORDER_ID --price 55` |
| Cancel order | `kalshi-cli orders cancel ORDER_ID` |
| Cancel all | `kalshi-cli orders cancel-all` |
| Batch create | `kalshi-cli orders batch-create --file orders.json` |
| List resting orders | `kalshi-cli orders list --status resting` |
| Queue position | `kalshi-cli orders queue ORDER_ID` |
| **Portfolio** |
| Balance | `kalshi-cli portfolio balance` |
| Positions | `kalshi-cli portfolio positions` |
| Fills | `kalshi-cli portfolio fills --limit 50` |
| Settlements | `kalshi-cli portfolio settlements` |
| **Subaccounts** |
| List | `kalshi-cli portfolio subaccounts list` |
| Create | `kalshi-cli portfolio subaccounts create` |
| Transfer | `kalshi-cli portfolio subaccounts transfer --from 1 --to 2 --amount 50000` |
| **Order Groups** |
| Create group | `kalshi-cli order-groups create --limit 100` |
| List groups | `kalshi-cli og list` |
| Update limit | `kalshi-cli order-groups update-limit GROUP_ID --limit 200` |
| Delete group | `kalshi-cli order-groups delete GROUP_ID` |
| **Block Trading** |
| Create RFQ | `kalshi-cli rfq create --market TICKER --qty 1000` |
| List RFQs | `kalshi-cli rfq list` |
| Create quote | `kalshi-cli quotes create --rfq RFQ_ID --price 65` |
| Accept quote | `kalshi-cli quotes accept QUOTE_ID` |
| **Streaming** |
| Live prices | `kalshi-cli watch ticker TICKER` |
| Orderbook deltas | `kalshi-cli watch orderbook TICKER` |
| Public trades | `kalshi-cli watch trades` |
| Your orders | `kalshi-cli watch orders` |
| Your fills | `kalshi-cli watch fills` |
| Your positions | `kalshi-cli watch positions` |
| **Exchange** |
| Exchange status | `kalshi-cli exchange status` |
| Schedule | `kalshi-cli exchange schedule` |
| Announcements | `kalshi-cli exchange announcements` |
| **Config** |
| Show config | `kalshi-cli config show` |
| Set value | `kalshi-cli config set output.format json` |
