# Simple Auction Simulation

This is a simple example of auction simulation to show the environment module of AgentScope.

## Background

This example simulates the following scenario:

Some bidders, each carrying their own money, participate in an auction. After the bidding for an item begins, they decide whether to bid a higher price after hearing the bids of others. When no one places a bid after the waiting time has elapsed, the auctioneer announces the auction results.

## How to Run

```shell
cd examples/environments/auction_simulation
python main.py
```

You can also set the following arguments:

- `bidder-num`: the number of bidders who participate in the auction.
- `agent-type`: `random` or `llm`, the agent type of bidders.
- `waiting-time`: the waiting time for the auctioneer to decide the winner.

The following is sample output:

```log
2024-08-13 14:52:26.056 | INFO     | listeners:__call__:43 - bidder_1 bid 20 for oil_painting
2024-08-13 14:52:26.799 | INFO     | listeners:__call__:86 - bidder_0 bid 25 for oil_painting
2024-08-13 14:52:27.744 | INFO     | listeners:__call__:86 - bidder_2 bid 30 for oil_painting
2024-08-13 14:52:28.434 | INFO     | listeners:__call__:86 - bidder_0 bid 35 for oil_painting
2024-08-13 14:52:28.863 | INFO     | listeners:__call__:86 - bidder_1 bid 100 for oil_painting
2024-08-13 14:52:31.865 | INFO     | env:sold:87 - oil_painting is sold to bidder_1 for 100
```