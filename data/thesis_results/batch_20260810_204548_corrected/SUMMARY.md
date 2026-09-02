# Batch metrics recalculated with current measure_data

Generated: 2026-08-30 15:51:29

Stored metrics come from the old run (double-counting bugs). Corrected
metrics are recalculated from the stored data with the current measure_data.

Corrected result copies: data/thesis_results/batch_20260810_204548_corrected/ (avg_metrics.py kann unveraendert auf diesem Verzeichnis laufen)
Recheck cross-check mismatches: 139
Reconstruction warnings: 2
Mismatches between rebuild and the counting-only recheck scripts:
- result_clean_00_20260810_204610.json strict_before entity: recheck 0.551724 vs rebuild 0.600000
- result_clean_00_20260810_204610.json loose_before entity: recheck 0.758621 vs rebuild 0.800000
- result_clean_00_20260810_205603.json strict_before entity: recheck 0.551724 vs rebuild 0.645161
- result_clean_00_20260810_205603.json loose_before entity: recheck 0.758621 vs rebuild 0.838710
- result_clean_00_20260810_210634.json strict_before entity: recheck 0.551724 vs rebuild 0.645161
- result_clean_00_20260810_210634.json strict_after entity: recheck 0.518519 vs rebuild 0.571429
- result_clean_00_20260810_210634.json loose_before entity: recheck 0.758621 vs rebuild 0.838710
- result_clean_00_20260810_210634.json loose_after entity: recheck 0.740741 vs rebuild 0.785714
- result_clean_01_20260810_204641.json strict_before entity: recheck 0.697674 vs rebuild 0.727273
- result_clean_01_20260810_204641.json loose_before entity: recheck 0.883721 vs rebuild 0.909091
- result_clean_01_20260810_205638.json strict_before entity: recheck 0.744186 vs rebuild 0.772727
- result_clean_01_20260810_205638.json loose_before entity: recheck 0.883721 vs rebuild 0.909091
- result_clean_01_20260810_210710.json strict_before entity: recheck 0.744186 vs rebuild 0.772727
- result_clean_01_20260810_210710.json loose_before entity: recheck 0.883721 vs rebuild 0.909091
- result_clean_02_20260810_204700.json strict_before entity: recheck 0.800000 vs rebuild 0.864865
- result_clean_02_20260810_204700.json loose_before entity: recheck 0.857143 vs rebuild 0.918919
- result_clean_02_20260810_205701.json strict_before entity: recheck 0.864865 vs rebuild 0.950000
- result_clean_02_20260810_205701.json loose_before entity: recheck 0.864865 vs rebuild 0.950000
- result_clean_02_20260810_210734.json strict_before entity: recheck 0.800000 vs rebuild 0.864865
- result_clean_02_20260810_210734.json loose_before entity: recheck 0.857143 vs rebuild 0.918919
Warnings: reconstructed before-dict deviates from the original run's input:
- result_text_noise_medium_substitution_20260810_210611.json strict_before: stored fp_total=12 vs 11 unique extras (duplicate keys in raw list; recomputed fp_name_in_gold uses the deduped set)
- result_text_noise_medium_substitution_20260810_210611.json loose_before: stored fp_total=8 vs 7 unique extras (duplicate keys in raw list; recomputed fp_name_in_gold uses the deduped set)

Full per-run numbers: corrected_metrics.json
