# Knowledge Graph Extraction Pipeline

Repository accompanying the bachelor thesis on knowledge graph extraction under noisy input conditions (TU Berlin). The project implements an LLM-based pipeline that extracts entities, relations, and triples from raw text, refines the extracted data (deduplication, alias merging), and evaluates the results against a DocRED-derived gold standard using loose entity matching.

## Repository Structure

| Path | Purpose |
|---|---|
| `src/` | Pipeline implementation: CLI, extraction, refinement, metrics |
| `data/` | Gold standards, input examples, experiment registry, thesis results |
| `data/registry/registry.json` | Single source of truth mapping experiments to input and gold files |
| `data/thesis_results/` | Batch runs and averaged metrics used in the thesis |
| `ai_generated_tools/` | AI-generated helper tools for running experiments and aggregating results |
| `tests/` | Unit and pipeline tests (incl. `tests/ai_generated_tests/`) |
| `requirements.txt` | Python dependencies |

Developer notes and old results are intentionally not part of the public repository; all working scripts are collected in `ai_generated_tools/`. Everything needed to understand the project and the thesis numbers is contained in this README and the tracked folders above.

## AI-Assisted Development

The code written outside `ai_generated_tools/` and `tests/ai_generated_tests/` in this project was written by me, with the AI tool acting as a programming assistant. The content in the marked folders is AI-generated but verified by me.

## Data

- **Gold standards** (`data/goldstandard_json_flat/`, `data/goldstandard_json_flat_with_types/`): four documents (`gold_00`–`gold_03`) in a DocRED-derived JSON schema containing `doc_id`, `aliases`, and `relations` (the `_with_types` variant adds entity types).
- **Input examples** (`data/inputexamples/`): raw texts per experiment category:
  - `clean/` — unmodified source texts
  - `coherence/` — block shuffle, random shuffle, combination, injection
  - `pro-forms/` — with and without pro-forms
  - `repetition/` — duplicated documents, entities, sentences
  - `text-noise/` — keyboard, OCR, and substitution noise at low/medium/high levels
- **Experiment registry** (`data/registry/registry.json`): 22 experiments, each mapping an `experiment_id` to an input file and a gold standard. The registry is the single source of truth for evaluation.

## Experiments and Thesis Scope

The thesis uses 19 of the 22 registered experiments. Excluded are the three substitution-noise experiments (`text_noise_low_substitution`, `text_noise_medium_substitution`, `text_noise_high_substitution`), which were cut from the evaluation plan due to time constraints. Their inputs, registry entries, and batch results remain in the repository.

The thesis reports **loose-matching metrics exclusively** (the pipeline computes both strict and loose variants). Reported metrics:

- Entity F1 — before and after refinement
- Triple F1 — before and after refinement
- Relation F1
- Cluster coverage — before and after refinement
- Average cluster hit — before and after refinement
- Duplicated cluster rate (share of gold clusters hit more than once)

These correspond to the following fields in the result files: `entity_f1`, `triple_f1`, `relation_f1`, `coverage`, `avg_cluster_hit`, `duplicated_rate`. The result files additionally contain `type_error_rate`, which is computed but not reported in the thesis.

## Thesis Results

`data/thesis_results/` contains the full batch run used for the thesis:

- `batch_20260810_204548_corrected/` — per-experiment folders with individual run results
- `batch_20260810_204548_corrected_avg.json` — averaged metrics per experiment (**canonical numbers used in the thesis**)

The uncorrected variant (`batch_20260810_204548*`) contains a triple-F1 bug that was discovered after generation; the corrected batch fixes this and is the authoritative one.

The helper tools in `ai_generated_tools/` automate this workflow:

- `run_all_experiments.py` — runs all registry experiments
- `avg_metrics.py` — averages metrics across runs
- `recompute_batch_metrics.py` — recomputes metrics for an existing batch
- `show_experiment.py` — displays results of a single experiment
- `debug_run.py` — single-experiment debug run

## Running the Pipeline

The thesis numbers require no execution — they are committed in `data/thesis_results/`. The instructions below are only needed to run the pipeline yourself, which requires a DeepSeek API key and incurs API costs (`show_experiment.py` works offline).

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set the API key for the extraction LLM (DeepSeek API):

   ```bash
   export DEEPSEEK_API_KEY=<your-key>
   ```

3. Run an experiment by its registry ID, e.g.:

   ```bash
   python -m app.main run clean_00
   ```

   Use `-o <dir>` to write the result JSON to a custom output directory. The result file contains extraction output, evaluation metrics (strict and loose, before and after refinement), and details.

## Tests

Run the test suite from the repository root:

```bash
pytest
```

Tests cover I/O, the pipeline, triple generation, metrics, and refinement. `tests/ai_generated_tests/` contains AI-generated tests (see the AI-Assisted Development section).
