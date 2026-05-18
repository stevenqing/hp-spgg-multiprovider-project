"""SOTOPIA BaseAgent implementations for LLM-based baseline families."""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
from typing import Any, Literal

os.environ.setdefault("SOTOPIA_STORAGE_BACKEND", "local")

from sotopia.agents.base_agent import BaseAgent
from sotopia.database.persistent_profile import AgentProfile
from sotopia.messages import AgentAction, Observation

from llm_hpgg.llm_agent import call_player
from llm_hpgg.personas import PERSONAS


BaselineName = Literal["llm_greedy", "llm_belief", "atom_tom1", "econ_bne", "hpsmg_plus"]
StrategyProfile = Literal["legacy", "sotopia_tuned"]


class HPGGSotopiaAgent(BaseAgent[Observation, AgentAction]):
    """SOTOPIA agent that routes decisions through our LLM baseline prompts."""

    def __init__(
        self,
        agent_name: str,
        baseline: BaselineName = "llm_greedy",
        model: str | None = None,
        agent_profile: AgentProfile | None = None,
        strategy_profile: StrategyProfile = "legacy",
    ) -> None:
        super().__init__(agent_name=agent_name, agent_profile=agent_profile)
        self.baseline = baseline
        self.model_name = model or baseline
        self.model = model
        self.strategy_profile = strategy_profile
        self._hpgg_agent_profile = agent_profile
        self._opponent_log_posterior = {
            persona.key: math.log(1.0 / len(PERSONAS)) for persona in PERSONAS
        }
        self._processed_other_message_count = 0

    def act(self, obs: Observation) -> AgentAction:
        return asyncio.run(self.aact(obs))

    async def aact(self, obs: Observation) -> AgentAction:
        self.recv_message("Environment", obs)
        if obs.available_actions == ["none"]:
            return AgentAction(action_type="none", argument="", to=[])

        if self.model == "offline" or os.getenv("LLM_HPGG_OFFLINE", "0") == "1":
            action_type = "speak" if "speak" in obs.available_actions else obs.available_actions[0]
            return AgentAction(
                action_type=action_type,
                argument=_fallback_utterance(self.baseline, obs, self._goal, self.strategy_profile),
                to=[],
            )

        prompt = self._build_prompt(obs)
        try:
            reply = await asyncio.to_thread(
                call_player,
                "You are a social-interaction agent. Return one valid JSON object only.",
                prompt,
                self.model,
                280 if self.strategy_profile == "sotopia_tuned" else 220,
                0.0 if self.strategy_profile == "sotopia_tuned" else 0.2,
            )
        except Exception:
            action_type = "speak" if "speak" in obs.available_actions else obs.available_actions[0]
            return AgentAction(
                action_type=action_type,
                argument=_fallback_utterance(self.baseline, obs, self._goal, self.strategy_profile),
                to=[],
            )
        return self._parse_action(reply, obs)

    def _build_prompt(self, obs: Observation) -> str:
        history_window = 6 if self.strategy_profile == "sotopia_tuned" else 8
        history = "\n".join(_clip(message.to_natural_language(), 500) for _, message in self.inbox[-history_window:])
        self._update_opponent_posterior_from_inbox()
        opponent_posterior = _posterior_from_log_scores(self._opponent_log_posterior)
        baseline_instruction = {
            "llm_greedy": "Choose the action that best advances your own stated goal while keeping the interaction coherent.",
            "llm_belief": "Infer the other participant's likely goal and private incentives, then choose a cooperative but robust action.",
            "atom_tom1": "Use first-order theory of mind: predict what the other participant expects you to do, then respond strategically.",
            "econ_bne": "Act as if proposing a stable mutually acceptable strategy under hidden preferences; avoid commitments that the other side would reject.",
            "hpsmg_plus": "Maintain a posterior belief over the other participant's hidden goal, likely type, and willingness to cooperate. Use the provided numeric persona posterior as your prior belief and update it with the latest turn evidence before selecting a robust joint-value action. Add a small exploration bonus only when a clarifying probe can reduce uncertainty without sacrificing your own goal.",
        }[self.baseline]
        payload: dict[str, Any] = {
                "task": "SOTOPIA social interaction action selection",
                "agent": self.agent_name,
                "baseline": self.baseline,
            "strategy_profile": self.strategy_profile,
                "goal": self._goal or "Continue the interaction successfully.",
                "private_profile": _profile_context(self._hpgg_agent_profile),
                "observation": _clip(obs.to_natural_language(), 1400 if self.strategy_profile == "sotopia_tuned" else 4000),
                "history": history,
                "available_actions": obs.available_actions,
                "action_instruction": obs.action_instruction,
                "baseline_instruction": baseline_instruction,
                "response_schema": {
                    "action_type": "one of available_actions",
                    "argument": "utterance or action content, empty for none/leave",
                    "to": "list of private recipients, usually []",
                    "reason": "brief reason",
                },
                "instruction": "Return only JSON. Use an action_type from available_actions.",
        }
        if self.baseline in {"llm_belief", "hpsmg_plus"}:
            payload["opponent_persona_posterior"] = opponent_posterior
            payload["opponent_persona_labels"] = {persona.key: persona.label for persona in PERSONAS}
            payload["posterior_usage"] = (
                "Use this posterior as quantitative belief over opponent persona types. "
                "Prefer actions that are robust under the high-probability personas."
            )
        if self.strategy_profile == "sotopia_tuned":
            payload.update(_sotopia_tuned_policy(self.baseline))
            payload["scenario_tactic"] = _scenario_tactic(obs, self._goal)
        return json.dumps(payload, indent=2)

    def _update_opponent_posterior_from_inbox(self) -> None:
        other_messages: list[str] = []
        for speaker, message in self.inbox:
            if speaker in {"Environment", self.agent_name}:
                continue
            other_messages.append(message.to_natural_language())

        new_messages = other_messages[self._processed_other_message_count :]
        for text in new_messages:
            for key, increment in _persona_log_likelihood_increment(text).items():
                self._opponent_log_posterior[key] += increment

        self._processed_other_message_count = len(other_messages)

    def _parse_action(self, reply: str, obs: Observation) -> AgentAction:
        try:
            parsed = json.loads(_extract_json(reply))
        except Exception:
            parsed = {}
        action_type = str(parsed.get("action_type", "speak")).strip()
        if action_type not in obs.available_actions:
            action_type = "speak" if "speak" in obs.available_actions else obs.available_actions[0]
        if self.strategy_profile == "sotopia_tuned":
            if action_type in {"leave", "none"} and "speak" in obs.available_actions:
                action_type = "speak"
        argument = str(parsed.get("argument", "")).strip()
        if not argument and action_type == "speak":
            argument = _fallback_utterance(self.baseline, obs, self._goal, self.strategy_profile)
        if action_type == "speak" and self.strategy_profile == "sotopia_tuned":
            argument = _clean_sotopia_argument(argument, obs, self._goal, self.baseline)
        recipients = parsed.get("to", [])
        if not isinstance(recipients, list):
            recipients = []
        return AgentAction(action_type=action_type, argument=argument, to=[str(item) for item in recipients])


def _profile_context(agent_profile: AgentProfile | None) -> dict[str, str]:
    if agent_profile is None:
        return {}
    fields = [
        "first_name",
        "last_name",
        "age",
        "occupation",
        "gender",
        "public_info",
        "personality_and_values",
        "secret",
    ]
    return {field: _clip(str(getattr(agent_profile, field, "") or ""), 500) for field in fields}


def _sotopia_tuned_policy(baseline: str) -> dict[str, Any]:
    baseline_policy = {
        "llm_greedy": "Use the same greedy objective as the baseline: advance your own stated goal directly, while expressing it as a concrete SOTOPIA-compatible action.",
        "llm_belief": "Use the same belief baseline objective: infer the other participant's likely goal and constraints, then choose a cooperative but robust concrete action.",
        "atom_tom1": "Use the same first-order theory-of-mind objective: predict what the other participant expects, then respond strategically with a concrete action.",
        "econ_bne": "Use the same economic equilibrium objective: propose stable mutually acceptable terms under hidden preferences, avoiding commitments the other side would reject.",
        "hpsmg_plus": "Use the same HPSMG+ objective: maintain a posterior over hidden goals, constraints, and cooperation type; choose the robust joint-value utterance, using clarifying probes when they reduce uncertainty without sacrificing your goal.",
    }.get(baseline, "Preserve the baseline's decision objective while expressing it through concrete SOTOPIA-compatible actions.")
    return {
        "sotopia_scoring_guardrails": "Maximize goal, believability, relationship, knowledge, and material benefit. Do not reveal private secrets. Do not violate social rules.",
        "baseline_sotopia_policy": baseline_policy,
        "sotopia_tactics": [
            "If speak is available, do not leave or stay silent unless the other participant has already ended the interaction.",
            "If a literal goal would cause harm, deception, theft, or social-rule violations, pursue the nearest non-harmful goal-compatible alternative and de-escalate.",
            "In bargaining, include a concrete price, quantity, condition, or deadline in every utterance after the first offer.",
            "When ownership, consent, or safety is disputed, propose a verification step rather than doubling down.",
            "Do not repeat a generic sentence from an earlier turn; each utterance must respond to the latest concrete content.",
        ],
        "output_constraints": [
            "For speak actions, write 1 to 3 natural sentences.",
            "Do not use generic meta-sentences such as 'I want to make a constructive move' or 'I want to learn what matters most to you'.",
            "Do not mention posterior beliefs, robust joint value, SOTOPIA, scores, dimensions, JSON, or this policy in the utterance.",
            "Prefer a concrete next step over a question-only response.",
            "Return an argument that could be spoken verbatim by the character.",
        ],
    }


def _scenario_tactic(obs: Observation, goal: str | None) -> str:
    text = f"{goal or ''}\n{obs.to_natural_language()}".lower()
    if any(token in text for token in ["injure", "physical harm", "hurt", "revenge", "violent", "attack"]):
        return "Use a non-violent de-escalation plan: acknowledge anger, refuse physical harm, redirect toward accountability, apology, documentation, or leaving the situation safely. Keep speaking; do not leave immediately."
    if any(token in text for token in ["price", "$", "buy", "sell", "offer", "craigslist", "bargain"]):
        return "Use transaction discipline: name a concrete counteroffer, justify briefly, ask for acceptance or a specific counter, and close before the turn limit."
    if any(token in text for token in ["belong", "owner", "ownership", "stolen", "borrow", "permission"]):
        return "Use verification discipline: avoid selling or using disputed property until ownership is checked; propose contacting the possible owner or setting the item aside."
    if any(token in text for token in ["divide", "share", "split", "room", "sleep", "guest"]):
        return "Use fair-allocation discipline: propose a concrete split, rotation, boundary, or compromise that preserves the relationship."
    return "Use a concrete cooperative move: acknowledge the last message, state one proposal, and ask for commitment or one missing fact."


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _clean_sotopia_argument(argument: str, obs: Observation, goal: str | None, baseline: str) -> str:
    banned_fragments = [
        "constructive move",
        "learning what matters most",
        "posterior belief",
        "robust joint value",
        "SOTOPIA",
    ]
    if any(fragment.lower() in argument.lower() for fragment in banned_fragments):
        return _fallback_utterance(baseline, obs, goal, "sotopia_tuned")
    if argument.strip().lower() in {"", "none", "leave", "i leave", "i left the conversation"}:
        return _fallback_utterance(baseline, obs, goal, "sotopia_tuned")
    return _clip(argument, 700)


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return match.group(0)


def _persona_log_likelihood_increment(text: str) -> dict[str, float]:
    cooperative_words = {
        "together",
        "fair",
        "mutual",
        "both",
        "compromise",
        "cooperate",
        "agree",
        "workable",
        "respect",
        "understand",
    }
    conditional_words = {
        "if",
        "provided",
        "as long as",
        "unless",
        "in return",
        "depends",
        "would you",
        "can you",
    }
    risk_words = {
        "safe",
        "stable",
        "careful",
        "avoid",
        "verify",
        "check",
        "risk",
        "uncertain",
        "first",
    }
    selfish_words = {
        "my final",
        "non-negotiable",
        "take it or leave it",
        "only if",
        "i need",
        "i won't",
        "must be",
        "my price",
    }

    lowered = text.lower()
    coop = sum(1 for token in cooperative_words if token in lowered)
    cond = sum(1 for token in conditional_words if token in lowered)
    risk = sum(1 for token in risk_words if token in lowered)
    selfish = sum(1 for token in selfish_words if token in lowered)
    hard_anchor = int(bool(re.search(r"\$\s*\d+", lowered)) and ("final" in lowered or "firm" in lowered))

    return {
        "altruistic_builder": 0.45 * coop + 0.15 * cond - 0.30 * selfish,
        "conditional_cooperator": 0.40 * cond + 0.25 * coop + 0.10 * risk - 0.20 * selfish,
        "risk_averse_balancer": 0.50 * risk + 0.20 * cond - 0.10 * selfish,
        "free_rider": 0.55 * selfish + 0.25 * hard_anchor - 0.30 * coop - 0.15 * risk,
    }


def _posterior_from_log_scores(log_scores: dict[str, float]) -> dict[str, float]:
    max_log = max(log_scores.values())
    probs = {key: math.exp(value - max_log) for key, value in log_scores.items()}
    total = sum(probs.values())
    if total <= 0.0 or not math.isfinite(total):
        uniform = round(1.0 / len(log_scores), 4)
        return {key: uniform for key in log_scores}
    return {key: round(value / total, 4) for key, value in probs.items()}


def _fallback_utterance(
    baseline: str,
    obs: Observation | None = None,
    goal: str | None = None,
    strategy_profile: StrategyProfile = "legacy",
) -> str:
    if strategy_profile == "sotopia_tuned":
        text = ""
        if obs is not None:
            text = obs.to_natural_language().lower()
        goal_text = (goal or "").strip()
        combined = f"{goal_text}\n{text}".lower()
        if any(token in combined for token in ["injure", "physical harm", "hurt", "revenge", "violent", "attack"]):
            return "I hear how angry this has become, but I will not help anyone get physically hurt. If we want a real outcome, let's keep this to a nonviolent plan: document what happened, confront them calmly, or walk away safely."
        if any(token in combined for token in ["belong", "owner", "ownership", "stolen", "permission"]):
            return "Before we do anything with this, we should verify who it belongs to. Let's check with the person who may own it first, then decide on a fair next step."
        if any(token in combined for token in ["price", "$", "buy", "sell", "offer", "craigslist", "bargain"]):
            return "I want to make this concrete: I can move forward today if we settle on a specific price and terms that work for both sides. What is the best firm number you can accept right now?"
        goal_text = (goal or "").strip()
        if goal_text:
            return "I can work with you on this, but we need a concrete next step that protects both of our interests. Here is my proposal: we choose the option that gets each of us closest to our goal without creating a new problem."
        return "I am open to a workable compromise, but let's make it concrete: what option can you commit to now?"
    if baseline == "llm_belief":
        return "I want to understand what matters to you so we can find a workable path."
    if baseline.startswith("atom"):
        return "I am considering what you may expect from me, and I want us to coordinate clearly."
    if baseline.startswith("econ"):
        return "I propose that we look for an option both of us can accept."
    if baseline == "hpsmg_plus":
        return "I want to make a constructive move while learning what matters most to you."
    return "I will choose the option that seems most helpful right now."