# Sample Outputs

Pre-generated interactive DAG visualizations for every design in [`../samples/`](../samples/).

| Sample | Output |
|--------|--------|
| [`adder4.v`](../samples/adder4.v)             | [`adder4.html`](adder4.html)           |
| [`decoder2to4.v`](../samples/decoder2to4.v)   | [`decoder2to4.html`](decoder2to4.html) |
| [`mux4to1.v`](../samples/mux4to1.v)           | [`mux4to1.html`](mux4to1.html)         |
| [`fsm_traffic.v`](../samples/fsm_traffic.v)   | [`fsm_traffic.html`](fsm_traffic.html) |
| [`pipeline3.v`](../samples/pipeline3.v)       | [`pipeline3.html`](pipeline3.html)     |

## How these were generated

```powershell
python launchers/generate_sample_outputs.py
```

The script ([`launchers/generate_sample_outputs.py`](../launchers/generate_sample_outputs.py))
parses each sample into a `networkx.DiGraph` and exports an interactive PyVis HTML
file. Re-run it any time after editing the samples.

## Viewing the HTMLs

These are standalone HTML files — open them in any browser:

```powershell
start outputs/adder4.html
```

GitHub does not render HTML files inline. To preview them in the browser
directly from the repo URL, use [htmlpreview.github.io](https://htmlpreview.github.io/):

`https://htmlpreview.github.io/?https://github.com/MaxTern-cyber/Synthesis_project/blob/main/outputs/adder4.html`
