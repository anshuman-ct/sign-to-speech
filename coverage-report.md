# Test Coverage Report

Generated from: sign-to-speech
Date: 2026-04-20
Framework detected: None (no test suite found)

## Summary

| Status | Module count | Notes |
|---|---|---|
| Covered | 0 | No test files found in project |
| Partial | 0 | — |
| Uncovered | 6 | All source modules have zero test coverage |

> ⚠️ WARNING: No test suite found. All outputs are inferred from source code
> and MUST be reviewed by a developer before the docs agent publishes any
> behavior as verified fact.

## Module Coverage

| Module | Status | Coverage score | Test file | Notes |
|---|---|---|---|---|
| src/config.py | uncovered | 0.00 | — | Configuration constants only; no testable logic |
| src/model.py | uncovered | 0.00 | — | CNN architecture builder; no unit tests |
| src/data_loader.py | uncovered | 0.00 | — | Data loading pipeline; no tests for CSV parsing or preprocessing |
| src/train.py | uncovered | 0.00 | — | Training orchestrator; no callback/history validation |
| src/evaluate.py | uncovered | 0.00 | — | Evaluation logic; no metrics validation |
| src/inference.py | uncovered | 0.00 | — | Real-time inference; no webcam/MediaPipe testing |

## Integration Test Coverage

No integration tests found.

## Unresolved Test Files

| Test file | Reason |
|---|---|---|
| — | No test files exist in this project |

## Coverage Gaps Requiring Human Review

All modules are uncovered. Review each behavior description before documenting.

- `src/config.py` — All constants need verification by developer
- `src/model.py` — Architecture decisions need verification
- `src/data_loader.py` — CSV loading and preprocessing need tests
- `src/train.py` — Training loop needs verification
- `src/evaluate.py` — Evaluation metrics need verification
- `src/inference.py` — Real-time inference needs integration testing

## Mock-Heavy Modules (Not Applicable)

None — no tests to analyze.

## Notes

This is a deep learning project where:
- Model training produces `.h5` checkpoint files
- Inference relies on OpenCV + MediaPipe (external dependencies)
- Test data lives in `data/raw/sign_mnist_*.csv`
- Results are visual (PNG plots, not assertions)

Traditional unit testing is minimal. The project's validation is done via:
- Training history accuracy/loss curves
- Test set accuracy from `evaluate.py`
- Confusion matrix visualization
- Manual inference testing via webcam