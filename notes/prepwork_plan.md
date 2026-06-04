Prepwork plan

- Layout: separate inputs folder (raw text per experiment) and gold folder (pure JSON per gold doc).
- Naming: use stable ids in filenames (experiment id, gold id) and reuse those ids everywhere.
- Registry: keep a small JSON registry mapping each experiment to its gold record.
- Registry fields: experiment_id, input_id or input_file, gold_id, optional gold_hash.
- Parsing: keep one canonical gold schema (doc_id, aliases, relations) and make the parser strict.
- Normalization: normalize alias strings consistently before matching.
