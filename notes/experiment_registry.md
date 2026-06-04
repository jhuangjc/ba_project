Experiment registry idea

- Keep a small JSON registry mapping each experiment to its goldstandard.
- For each experiment record: experiment_id, input_file, gold_id, gold_file.
- Use the registry as the single source of truth when running metrics.
- Still validate mapping at runtime (doc_id or gold hash) to catch mismatches.
- With ~10 experiments and 4 gold datapoints, manual edits are fine.
