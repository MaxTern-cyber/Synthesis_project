# Sample Outputs

Pre-generated interactive DAG visualizations for every design in [`../samples/`](../samples/).

| Sample | Output | Scale |
|--------|--------|-------|
| [`adder4.v`](../samples/adder4.v)             | [`adder4.html`](adder4.html)           | 34 nodes / 37 edges |
| [`decoder2to4.v`](../samples/decoder2to4.v)   | [`decoder2to4.html`](decoder2to4.html) | 15 nodes / 20 edges |
| [`mux4to1.v`](../samples/mux4to1.v)           | [`mux4to1.html`](mux4to1.html)         | 20 nodes / 25 edges |
| [`fsm_traffic.v`](../samples/fsm_traffic.v)   | [`fsm_traffic.html`](fsm_traffic.html) | 9 nodes / 10 edges  |
| [`pipeline3.v`](../samples/pipeline3.v)       | [`pipeline3.html`](pipeline3.html)     | 12 nodes / 20 edges |
| [`array_mult8.v`](../samples/array_mult8.v)   | [`array_mult8.html`](array_mult8.html) | **326 nodes / 489 edges** |
| [`array_mult16.v`](../samples/array_mult16.v) | [`array_mult16.html`](array_mult16.html) | **1278 nodes / 1985 edges** |

## How these were generated

```powershell
python launchers/generate_sample_outputs.py
```

The script ([`launchers/generate_sample_outputs.py`](../launchers/generate_sample_outputs.py))
parses each sample into a `networkx.DiGraph` and exports an interactive PyVis HTML
file. Re-run it any time after editing the samples.

## Viewing the HTMLs

These are standalone HTML files -- open them in any browser:

```powershell
start outputs/adder4.html
```

GitHub does not render HTML files inline. To preview them in the browser
directly from the repo URL, use [htmlpreview.github.io](https://htmlpreview.github.io/):

`https://htmlpreview.github.io/?https://github.com/MaxTern-cyber/Synthesis_project/blob/main/outputs/adder4.html`
