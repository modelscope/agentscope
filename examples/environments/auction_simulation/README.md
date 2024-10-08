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
- `use-dist`: whether to use the distributed version. (You have to shut down the simulation manually in the distributed version.)

The following is sample output:

```log
Auction: Auction starts!
Listener: Notifying the bidder bidder_0...
Listener: Notifying the bidder bidder_1...
Listener: Notifying the bidder bidder_2...
Listener: Notifying the bidder bidder_3...
Listener: Notifying the bidder bidder_4...
bidder_1: Bid 34 for oil_painting
Listener: Bidder bidder_1 bids 34 for oil_painting. Notifying Bidder bidder_0
Listener: Bidder bidder_1 bids 34 for oil_painting. Notifying Bidder bidder_2
Listener: Bidder bidder_1 bids 34 for oil_painting. Notifying Bidder bidder_3
Listener: Bidder bidder_1 bids 34 for oil_painting. Notifying Bidder bidder_4
...
bidder_1: Bid 88 for oil_painting
Listener: Bidder bidder_1 bids 88 for oil_painting. Notifying Bidder bidder_0
bidder_0: Bid 53 for oil_painting
Listener: Bidder bidder_1 bids 88 for oil_painting. Notifying Bidder bidder_2
Listener: Bidder bidder_1 bids 88 for oil_painting. Notifying Bidder bidder_3
Listener: Bidder bidder_1 bids 88 for oil_painting. Notifying Bidder bidder_4
bidder_3: Not bid for oil_painting
bidder_0: Not bid for oil_painting
bidder_3: Bid 35 for oil_painting
bidder_4: Bid 21 for oil_painting
bidder_0: Not bid for oil_painting
bidder_1: Bid 26 for oil_painting
bidder_2: Not bid for oil_painting
Auction: Auction ends!
Auction: oil_painting is sold to bidder_1 for 88
```
