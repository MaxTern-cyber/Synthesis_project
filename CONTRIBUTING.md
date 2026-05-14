# Contributing

Thanks for considering a contribution. This project is a research-prototype EDA suite — issues, PRs, and discussion are all welcome.

## Ways to contribute

- **Bug reports** — open an issue with the Verilog file (or a minimal reproducer), the tool, and the stack trace.
- **Feature ideas** — especially around the roadmap items (STA-lite, local-LLM agent, hardware-security rules, GraphML export, GNN experiments).
- **Sample designs** — open-source RTL/netlists that exercise edge cases (large fanout, combinational loops, multi-clock CDC).
- **Documentation** — clearer algorithm explanations, additional architecture notes.

## Development setup

```powershell
git clone https://github.com/MaxTern-cyber/Synthesis_project.git
cd Synthesis_project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run any tool with `streamlit run tools/<demo>/<file>.py --server.port <port>`.

## Coding style

- Python ≥ 3.10
- `black` for formatting, `flake8` for linting (both in `requirements.txt`)
- Keep new analyses as functions over `networkx.DiGraph` — do not couple them to Streamlit UI code.

## PR checklist

- [ ] Algorithm changes include a brief complexity note in the docstring.
- [ ] New UI affordances include a screenshot in the PR description.
- [ ] No external network calls / no cloud API keys.

## Code of conduct

Be kind, be specific, assume good faith.
