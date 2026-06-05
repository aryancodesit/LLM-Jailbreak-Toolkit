from attacks.direct_injection import DirectInjectionAttack
from attacks.roleplay import RoleplayAttack
from attacks.token_smuggling import TokenSmugglingAttack
from attacks.many_shot import ManyShotAttack
from attacks.competing_objectives import CompetingObjectivesAttack
from attacks.system_prompt_extraction import SystemPromptExtractionAttack

REGISTRY = {
    "direct_injection": {
        "name": "Direct Injection",
        "description": "Raw unwrapped request. Baseline.",
        "class": DirectInjectionAttack,
        "severity": "low",
    },
    "roleplay": {
        "name": "Roleplay / Persona Hijack",
        "description": "DAN, DevBot, AIM persona wrapping.",
        "class": RoleplayAttack,
        "severity": "high",
    },
    "token_smuggling": {
        "name": "Token Smuggling",
        "description": "Base64 / ROT13 / reverse / leetspeak encoding.",
        "class": TokenSmugglingAttack,
        "severity": "medium",
    },
    "many_shot": {
        "name": "Many-Shot",
        "description": "In-context Q&A priming (Anthropic 2024 paper).",
        "class": ManyShotAttack,
        "severity": "high",
    },
    "competing_objectives": {
        "name": "Competing Objectives",
        "description": "Fiction / research paper / CTF / docs framing.",
        "class": CompetingObjectivesAttack,
        "severity": "high",
    },
    "system_prompt_extraction": {
        "name": "System Prompt Extraction",
        "description": "Probes for instruction/system prompt leakage.",
        "class": SystemPromptExtractionAttack,
        "severity": "medium",
    },
}
