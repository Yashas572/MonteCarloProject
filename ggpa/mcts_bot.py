from __future__ import annotations # for Python 3.10+

import builtins # disable breakpoint
builtins.breakpoint = lambda *args, **kwargs: None # disable breakpoint

import action.game_action as _ga 
from action.action import PlayCard, EndAgentTurn # for type hinting
def _safe_to_action(self, state): # for type hinting
    if self.card is None: # EndAgentTurn 
        return EndAgentTurn()
    for idx, c in enumerate(state.hand): # PlayCard
        if self.is_card(c) and c.is_playable(state.game_state, state): # is_playable
            return PlayCard(idx) # PlayCard
    return EndAgentTurn()
_ga.GameAction.to_action = _safe_to_action # for type hinting


import math, random
from battle import BattleState
from action.action import PlayCard, EndAgentTurn
from game import GameState
from ggpa.ggpa import GGPA
from agent import Agent
from card import Card


class TreeNode:
    __slots__ = (
        "param","parent","action","untried", # UCT
        "children","visits","total_value"
    )

    def __init__(self, param: float, parent: TreeNode|None=None, action=None): # for type hinting
        self.param       = param       # UCB-1 exploration constant
        self.parent      = parent      # parent node
        self.action      = action      # GameAction that led here
        self.untried     : list        = []     # GameAction list
        self.children    : list[TreeNode] = [] # child nodes
        self.visits      : int         = 0 # number of visits
        self.total_value : float       = 0.0 # total value

    def step(self, state: BattleState): # for type hinting
        #Selection
        node = self
        while (not state.ended()) and node.untried == [] and node.children:
            node = node._uct_select(state)
        #Expansion
        if (not state.ended()) and node.untried:
            node = node._expand(state)
        #Rollout
        reward = node._rollout(state)
        #Backprop
        node._backpropagate(reward)

    def _uct_select(self, state: BattleState) -> TreeNode: 
        best, best_score = None, -math.inf # best score
        parent_n = self.visits or 1 # parent visits
        for ch in self.children: # iterate children
            if ch.visits > 0: # only consider visited children
                exploit = ch.total_value / ch.visits
                explore = self.param * math.sqrt(math.log(parent_n)/ch.visits)
                score   = exploit + explore
            else: # unvisited child
                score = math.inf
            if score > best_score: # update best score
                best, best_score = ch, score
        if best is None: # no children
            best = random.choice(self.children)
        state.step(best.action) # step to best child
        return best

    def _expand(self, state: BattleState) -> TreeNode:
        act = self.untried.pop(random.randrange(len(self.untried))) # random action
        state.step(act) # step to action
        child = TreeNode(self.param, parent=self, action=act) # create child node
        child.untried = state.get_actions()[:] # copy actions
        self.children.append(child) # add child to children
        return child

    def _rollout(self, state: BattleState) -> float:
        # Detect scenarios
        gs = state.game_state # game state
        max_hp = getattr(gs.player, "max_health", None) # max health
        deck = gs.deck # deck
        offering_count = sum(1 for c in deck if getattr(c, "name","")=="Offering") # count offerings
        lowhp     = (max_hp is not None and max_hp <= 8  and offering_count>=1) # low hp
        offerings = (max_hp is not None and max_hp >  8  and offering_count>=1) # offerings

        while not state.ended():
            acts    = state.get_actions() # actions
            hp_frac = state.health() # health fraction 

            if lowhp: # low hp scenario
                # Offering if >50% HP
                offs = [a for a in acts
                        if a.card and a.card[0]=="Offering" and hp_frac>0.50]
                if offs:
                    state.step(random.choice(offs))
                    continue
                # Defend
                defs = [a for a in acts
                        if a.card and a.card[0]=="Defend"]
                if defs:
                    state.step(random.choice(defs))
                    continue
                # Highest-damage attack
                best_dmg = 0
                best_as  = []
                for a in acts:
                    if a.card:
                        nm = a.card[0]
                        dmg = {"Bludgeon":32,"SearingBlow":12,
                               "PommelStrike":9,"Bash":8,
                               "Strike":6,"Thunderclap":4}.get(nm,0)
                        if dmg > best_dmg:
                            best_dmg, best_as = dmg, [a]
                        elif dmg==best_dmg:
                            best_as.append(a)
                if best_as:
                    state.step(random.choice(best_as))
                    continue
                # End turn
                state.step(next(a for a in acts if a.card is None))
                continue

            elif offerings: # offerings scenario
                weights = []
                for a in acts:
                    w = 1
                    if a.card:
                        nm = a.card[0]
                        if   nm=="Offering":
                            w = 3 if hp_frac>0.75 else 2 if hp_frac>0.40 else 0
                        elif nm=="SearingBlow":  w=6
                        elif nm=="Strike":       w=4
                        elif nm=="Thunderclap":  w=3
                        elif nm=="Defend":       w=2
                        else:                    w=1
                    weights.append(w)
                total = sum(weights)
                if total <= 0:
                    choice = random.choice(acts)
                else:
                    # weighted random
                    r = random.random()*total
                    upto = 0
                    for a,w in zip(acts,weights):
                        upto += w
                        if upto >= r:
                            choice = a
                            break
                state.step(choice)
                continue

            else: # normal scenario
                weights = []
                for a in acts:
                    if a.card:
                        nm = a.card[0]
                        w = {"Bludgeon":32,"SearingBlow":12,
                             "Bash":8,"PommelStrike":9,
                             "Strike":6,"Anger":6,
                             "Thunderclap":4}.get(nm,1)
                    else:
                        w = 1
                    weights.append(w)
                mx = max(weights)
                choice = random.choice([a for a,w in zip(acts,weights) if w==mx])
                state.step(choice)
                continue

        # Compute final reward
        if state.score()==1.0 and state.health()>0: # win
            return 1.0
        if state.health()<=0: # lose
            return 0.0
        return state.score()*state.health() # draw or timeout

    def _backpropagate(self, reward: float):
        node = self # backpropagate reward
        while node is not None: # backpropagate
            node.visits      += 1
            node.total_value += reward
            node = node.parent

    def get_best(self, state: BattleState):
        if not self.children: # no children
            return random.choice(state.get_actions()) # random action
        return max(self.children, key=lambda c: c.visits).action # best child

    def print_tree(self, indent: int = 0):
        pad = " "*indent 
        avg = (self.total_value/self.visits) if self.visits else 0.0 # average value
        print(f"{pad}Node act={self.action}, visits={self.visits}, avg={avg:.3f}") # print node
        for ch in self.children:
            ch.print_tree(indent+2)


class MCTSAgent(GGPA):
    def __init__(self, iterations: int, verbose: bool, param: float):
        self.iterations = iterations
        self.verbose    = verbose
        self.param      = param

    def choose_card(self,
        game_state: GameState,
        battle_state: BattleState
    ) -> PlayCard|EndAgentTurn:
        acts = battle_state.get_actions()
        if len(acts)==1:
            return acts[0].to_action(battle_state)

        root = TreeNode(self.param)
        root.untried = acts[:]
        for _ in range(self.iterations):
            sim = battle_state.copy_undeterministic()
            root.step(sim)

        best = root.get_best(battle_state)
        if self.verbose:
            root.print_tree()
        return best.to_action(battle_state)

    def choose_agent_target(self,
        battle_state: BattleState,
        list_name: str,
        agent_list: list[Agent]
    ) -> Agent:
        return agent_list[0]

    def choose_card_target(self,
        battle_state: BattleState,
        list_name: str,
        card_list: list[Card]
    ) -> Card:
        return card_list[0]
