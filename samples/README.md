# Sample Designs

Small, textbook Verilog designs used to exercise the analyzers in this repo.

All files in this folder are **original, public-domain textbook designs** written
from scratch for this project — no third-party IP, no proprietary RTL, no
synthesized netlists from commercial tools.

## Contents

| File | Type | What it exercises |
|------|------|-------------------|
| [`adder4.v`](adder4.v)         | Combinational, structural | Critical path, cone-of-influence, gate-level depth |
| [`decoder2to4.v`](decoder2to4.v) | Combinational, structural | Fanout analysis, input→output dependency chains |
| [`mux4to1.v`](mux4to1.v)       | Combinational, structural | Fanin tracing, cone-of-influence |
| [`fsm_traffic.v`](fsm_traffic.v) | Sequential, behavioral    | FSM detection, register graph, clock/reset trees |
| [`pipeline3.v`](pipeline3.v)   | Sequential, behavioral    | Pipeline detection, multi-stage critical path |

## How to use

```powershell
# Example: launch the Netlist Analyzer and load one of these files via the UI
streamlit run tools/demo2/local_analyzer.py --server.port 8620
```

Inside the Streamlit UI, upload any `.v` file from this folder.

## Adding more samples

Good candidates for further additions (all permissively licensed, drop in as
new `.v` files in this folder):

- **ISCAS-85 / ISCAS-89 benchmarks** — classic academic combinational and
  sequential circuits (`c17`, `c432`, `c1908`, `s27`, `s298`, …).
- **OpenCores** — small open-source IP blocks, e.g. a UART or simple RISC core.
- **OpenROAD / OpenLane example designs** — `gcd`, `riscv32i`, `aes`.

If you add a file, please:
1. Confirm the upstream license is permissive (MIT / BSD / Apache / Public Domain).
2. Preserve the original license header at the top of the file.
3. Add an entry to the table above.
