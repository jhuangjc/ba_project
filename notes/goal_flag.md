Goal: Metrics flag

- Add a CLI flag to the existing generate command to trigger metrics.
- Keep the default output as entities + triples; append metrics only when flag is set.
- Require a gold reference (gold file or experiment registry lookup) when flag is used.
