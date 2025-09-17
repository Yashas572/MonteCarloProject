# Monte Carlo Card Battle Simulator

## Project Overview
The Monte Carlo Card Battle Simulator is a Python-based game simulation framework I developed to explore AI-driven decision-making in turn-based strategy games.  
Inspired by the battle mechanics of *Slay the Spire*, this project models the core combat loop of a deck-building roguelike and provides a modular, extensible environment for experimenting with new cards, rules, and intelligent agents.

The system is designed for rapid prototyping and algorithmic experimentation, making it a practical testbed for:
- Monte Carlo Tree Search (MCTS)–based decision-making
- Heuristic and rule-based AI agents
- Dynamic rule and card system design

---

## Key Highlights
- End-to-end game simulation implementing the full player–enemy turn cycle, including energy management, card draws, and enemy intent prediction.
- AI agent integration with support for pluggable agents (MCTS, heuristic, or language-model-driven) for automated gameplay.
- Extensible card framework allowing new cards to be defined by combining modular actions, targets, and status effects.
- Headless execution for fast iteration and large-scale simulations.
- Deterministic testing with seeded randomness for reproducible experiments.

---

## Technical Stack
- **Language:** Python 3
- **Core Modules:** `agent.py`, `battle.py`, `card.py`, `game.py`, `status_effects.py`, `utility.py`
- **AI Techniques:** Monte Carlo Tree Search, heuristic evaluation
- **Architecture:** Modular, object-oriented design for easy extension

---

## How It Works
1. **Initialize Game State** – Player and enemies start with defined HP, decks, and status effects.
2. **Turn Loop**:
   - Player gains energy and draws cards.
   - AI or human agent selects cards to play based on available energy.
   - Remaining cards are discarded; enemies execute their intended actions.
3. **Victory/Loss Conditions** – Battle ends when all enemies or the player reach 0 HP.

---

## Potential Applications
- AI research and benchmarking of decision-making algorithms in a controlled environment.
- Game design prototyping for testing new card mechanics without building a full game.
- Algorithm evaluation by comparing MCTS against heuristic or random play.

---

## Future Enhancements
- Additional enemy types and behaviors.
- Multi-act progression and map navigation.
- Integration of reinforcement learning agents for adaptive play.
