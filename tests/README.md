# Tests

This directory contains the test suite for the PoorNull package.

The test structure mirrors the source code structure:

```
tests/
├── data/
│   ├── test_download.py      # Tests for data download functions
│   └── test_constants.py     # Tests for constants module
├── indicators/
│   └── test_macd.py          # Tests for MACD indicator functions
├── conftest.py               # Shared pytest fixtures and configuration
└── README.md                 # This file
```

## Running Tests

To run all tests:

```bash
pytest
```

To run tests with verbose output:

```bash
pytest -v
```

To run tests for a specific module:

```bash
pytest tests/data/
pytest tests/indicators/
```

To run a specific test file:

```bash
pytest tests/data/test_download.py
```

To run a specific test:

```bash
pytest tests/data/test_download.py::TestPeriod::test_period_values
```

## Test Coverage

The tests cover:

1. **Data Download Module**:
   - Period enum values
   - Download functions for all timeframes (daily, weekly, monthly, quarterly)
   - Error handling (empty data, missing columns)
   - Parameter passing (adjust, period)

2. **MACD Indicators**:
   - MACD calculation with default and custom parameters
   - Column validation
   - Date sorting
   - Crossover detection (golden cross, death cross)
   - Error handling

3. **Constants**:
   - Column mapping definitions
   - Mapping correctness

## Notes

- Tests use mocking to avoid network calls for data download tests
- MACD tests use synthetic data to ensure deterministic results
- All tests should run quickly without external dependencies
