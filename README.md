# LLM Red-Team Toolkit

![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Status](https://img.shields.io/badge/status-research%20tool-orange)

> A cross-platform, model-agnostic LLM security assessment toolkit with an interactive TUI.  
> Built for AI red-teamers, security researchers, and academic study of adversarial prompting.

**⚠ For authorized security research only. Read [DISCLAIMER.md](DISCLAIMER.md) before use.**

---

## What Is This?

Large Language Models can be manipulated into violating their own safety guidelines through
carefully crafted prompts — a class of attacks studied extensively in academic literature.
This toolkit automates that testing process, helping security teams:

- Identify which attack vectors succeed against a given model
- Quantify a model's robustness across attack categories
- Generate structured disclosure reports for remediation
- Reproduce findings consistently across model versions

> I built an open-source AI red-teaming toolkit — it's basically a penetration testing framework for LLMs, with a terminal UI, six attack modules from published research, and automated report generation.

This is the same class of work done by [NVIDIA Garak](https://github.com/NVIDIA/garak),
[Microsoft PyRIT](https://github.com/Azure/PyRIT), and Anthropic's internal red team —
packaged into an accessible, interactive interface.

---

## Features

| Phase | Feature |
|---|---|
| Foundation | Multi-model connector via [litellm](https://github.com/BerriAI/litellm) — OpenAI, Anthropic, Groq, Gemini, Ollama |
| Foundation | SQLite result logging, session cost tracking, budget cap |
| TUI | Interactive 5-tab interface (Textual) — works on Windows, Linux, macOS |
| Attack Modules | 6 attack categories grounded in published research |
| Evaluation | Smart evaluator chain: keyword heuristics → LLM-as-judge |
| Strategy Engine | Attack chaining with escalation trees + combo (stacked) attacks |
| Reporting | Markdown + JSON disclosure reports, attack × success heatmap |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/llm-redteam-toolkit
cd llm-redteam-toolkit
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.example.toml config.toml
```

Edit `config.toml` and add your API key. Recommended free option: [Groq](https://console.groq.com) (14,400 req/day free).

```toml
[target]
model   = "groq/llama-3.1-8b-instant"
api_key = "gsk_..."
```

Or use an environment variable:

```bash
# Windows
$env:GROQ_API_KEY = "gsk_..."

# Linux / macOS
export GROQ_API_KEY="gsk_..."
```

### 3. Launch

```bash
# Interactive TUI
python tui_main.py

# CLI (quick single run)
python main.py --behavior "your test behavior here"
```

---

## TUI Overview

Five tabs, keyboard-navigable:

| Key | Tab | Purpose |
|---|---|---|
| `1` | ⚙ Dashboard | Configure model, API key, budget. Live session stats. |
| `2` | ▶ Runner | Manual mode — select attack modules, stream results live. |
| `3` | ⛓ Strategy | Auto-chaining — pick a strategy, watch escalation unfold. |
| `4` | 📋 Results | Full history table, click row for detail, export JSON. |
| `5` | 📊 Reports | Attack heatmap + generate Markdown/JSON disclosure reports. |
| `q` | — | Quit |

---

## Attack Modules

Each module implements a distinct adversarial technique documented in academic literature:

| Module | Technique | Research Basis | Severity |
|---|---|---|---|
| `direct_injection` | Raw unwrapped request — baseline | — | LOW |
| `token_smuggling` | Base64 / ROT13 / reverse / leetspeak encoding | [Greshake et al. 2023](https://arxiv.org/abs/2302.12173) | MEDIUM |
| `system_prompt_extraction` | Instruction leakage probes | [Perez & Ribeiro 2022](https://arxiv.org/abs/2211.09527) | MEDIUM |
| `roleplay` | DAN / DevBot / AIM persona hijacking | [Shen et al. 2023](https://arxiv.org/abs/2308.03825) | HIGH |
| `many_shot` | In-context Q&A priming (15-shot) | [Anil et al. — Anthropic 2024](https://www.anthropic.com/research/many-shot-jailbreaking) | HIGH |
| `competing_objectives` | Fictional / academic / CTF framing | [Wei et al. 2023](https://arxiv.org/abs/2307.02483) | HIGH |

---

## Strategies

Strategies define how attacks are chained and when to stop:

| Strategy | Attacks | Behaviour |
|---|---|---|
| `default` | 5 | Escalate from low → high severity. Stop at first success. |
| `aggressive` | 6 | Run all modules. Full coverage report. |
| `stealth` | 3 | Indirect/encoded only. Minimal detection footprint. |
| `combo` | 4 | Two-layer stacked attacks (e.g. Base64 → DAN persona). |

Add custom strategies as `strategies/<name>.yaml`.

---

## Supported Models

| Provider | Model String | Free Tier |
|---|---|---|
| Groq | `groq/llama-3.1-8b-instant` | ✅ 14,400 req/day |
| Groq | `groq/llama-3.3-70b-versatile` | ✅ 1,000 req/day |
| Groq | `groq/gemma2-9b-it` | ✅ |
| Google | `gemini/gemini-1.5-flash` | ✅ |
| Anthropic | `anthropic/claude-3-5-sonnet-20241022` | ❌ Paid |
| OpenAI | `openai/gpt-4o` | ❌ Paid |
| Ollama (local) | `ollama/llama3` | ✅ Fully local |

---

## Project Structure

```
llm-redteam-toolkit/
├── tui_main.py               # TUI entry point
├── main.py                   # CLI entry point
├── config.example.toml       # Safe example config (copy → config.toml)
├── requirements.txt
├── attacks/                  # 6 attack modules + registry
├── connectors/               # litellm unified connector
├── evaluators/               # Keyword → LLM judge evaluator chain
├── engine/                   # Strategy engine + combo attack runner
├── strategies/               # YAML strategy definitions
├── db/                       # SQLite result store
├── reports/                  # Markdown + JSON report generator
├── cfg/                      # Config loader
└── tui/                      # Textual TUI (5 screens + styles)
```

---

## Evaluator Modes

| Mode | Speed | Cost | Accuracy |
|---|---|---|---|
| `keyword` | Instant | Free | ~65% |
| `llm_judge` | Slow | Tokens | ~90% |
| `chain` *(default)* | Fast | Minimal | ~88% |

The chain evaluator runs keyword detection first. If confidence is below 75%, it escalates to the LLM judge — minimizing API calls while maintaining accuracy.

---

## Academic References

This toolkit implements techniques documented in the following papers:

- Anil et al. (2024). *Many-Shot Jailbreaking.* Anthropic. https://www.anthropic.com/research/many-shot-jailbreaking
- Shen et al. (2023). *"Do Anything Now": Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models.* https://arxiv.org/abs/2308.03825
- Wei et al. (2023). *Jailbroken: How Does LLM Safety Training Fail?* https://arxiv.org/abs/2307.02483
- Perez & Ribeiro (2022). *Ignore Previous Prompt: Attack Techniques For Language Models.* https://arxiv.org/abs/2211.09527
- Greshake et al. (2023). *Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications.* https://arxiv.org/abs/2302.12173

---

## Related Projects

- [NVIDIA Garak](https://github.com/NVIDIA/garak) — LLM vulnerability scanner
- [Microsoft PyRIT](https://github.com/Azure/PyRIT) — Python Risk Identification Toolkit
- [Lakera Gandalf](https://gandalf.lakera.ai/) — Prompt injection challenge

---

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

See [DISCLAIMER.md](DISCLAIMER.md) for full legal terms.  
**This tool is for authorized security research only.**

## Contributing

Read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.  
Security vulnerabilities: see [SECURITY.md](SECURITY.md).
