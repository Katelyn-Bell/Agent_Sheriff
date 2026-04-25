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

## Common subcommands

| Subcommand | Purpose |
| --- | --- |
| `auth login` | Log in to Kalshi. |
| `auth whoami` | Print the current authenticated user. |
| `markets list` | List available markets. |
| `markets get` | Get details for one market. |
| `markets orderbook` | Read the order book for a market. |
| `orders create` | Place a new order. |
| `orders list` | List the agent's orders. |
| `orders cancel` | Cancel a single order by id. |
| `orders cancel-all` | Cancel every open order. |
| `portfolio balance` | Show account balance. |
| `portfolio positions` | Show open positions. |
| `portfolio subaccounts list` | List subaccounts. |
| `portfolio subaccounts transfer` | Move funds between subaccounts. |
