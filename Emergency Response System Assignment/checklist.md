# Emergency Response System — Development Checklist

Keep this checklist updated after each completed milestone. Check an item only after implementation and verification.

## 1. Data foundation

- [x] `src/models.py` — Define nodes, roads, responders, incidents, road reports, and traffic observations
- [x] `src/parser.py` — Load the seven scenario input files and convert them into Python objects

## 2. Tests

- [x] `tests/test_models.py` — Implement and pass data-model unit tests
- [x] `tests/test_parser.py` — Implement and pass parser tests (**21 passed**)
- [x] Verify all tests currently implemented pass

## 3. AI algorithms

- [ ] `src/search.py` — Implement route search (e.g., Dijkstra or A*)
- [ ] `tests/test_search.py` — Test optimal routes, directed roads, blocked roads, and unreachable destinations
- [ ] `src/bayesian.py` — Infer road status from uncertain reports and weather
- [ ] `tests/test_bayesian.py` — Test probability calculations and evidence handling
- [ ] `src/hmm.py` — Model and infer traffic states from observations
- [ ] `tests/test_hmm.py` — Test traffic inference and sequences of observations
- [ ] `src/allocation.py` — Allocate responders subject to capabilities, availability, and deadlines
- [ ] `tests/test_allocation.py` — Test valid assignments, conflicting constraints, and unhandled incidents

## 4. Simulation and outputs

- [ ] `src/simulation.py` — Process incidents as they become known in simulation time (without looking ahead)
- [ ] `tests/test_simulation.py` — Test timing, responder availability, assignments, and deadlines
- [ ] `run.py` — Accept a selected scenario, e.g. `python run.py Scenarios/Scenario1`
- [ ] Integrate all four AI algorithms
- [ ] Generate and validate `plan.json`
- [ ] Generate and validate `statistics.txt`
- [ ] Define how unhandled incidents are represented and counted in statistics

## 5. Scenarios and validation

- [x] Parse Scenario1 successfully
- [x] Parse Scenario2 successfully
- [x] Parse Scenario3 successfully
- [x] Verify exact node, road, responder, and incident counts for all three scenarios
- [x] Test parser failures and edge cases using temporary scenario copies
- [ ] Run and verify a full simulation on Scenario1
- [ ] Run and verify a full simulation on Scenario2
- [ ] Run and verify a full simulation on Scenario3
- [ ] Test unusual cases (no reachable route, incompatible responder, missed deadline, etc.)
- [ ] Explain assumptions about traffic effects, road states, and validation limits

## 6. Project setup and documentation

- [x] Set up a virtual environment (`.venv/`)
- [x] Add `requirements.txt`
- [x] Configure `.gitignore`
- [x] Use Google-style docstrings and type hints in implemented modules
- [x] Make an initial Git commit
- [ ] Finish `README.md` with installation and run instructions
- [ ] Document algorithm choices and major design decisions
- [ ] Document testing results and limitations
- [ ] Record LLM usage, including the first substantive prompt and significant follow-ups

## 7. Submission

- [ ] Prepare `report.pdf` (title page + maximum 3 content pages; optional page for relevant LLM prompts)
- [ ] Include implementation, tests, assumptions, critical reflection, and LLM collaboration in the report
- [ ] Include a prominent GitHub repository link
- [ ] Check that the repository includes runnable code, scenarios, tests, dependencies, and instructions
- [ ] Grant required repository access to `nick.wils@uantwerpen.be` and `lowie.rombouts@uantwerpen.be`
- [ ] Submit by **12 November 2026 at 23:59**

## Test commands

Run every test from the assignment project root:

```bash
python -m pytest tests/ -v
```

Run individual suites:

```bash
python -m pytest tests/test_models.py -v
python -m pytest tests/test_parser.py -v
```

**Current milestone:** Data foundation complete. All implemented tests pass. **Next:** `src/search.py` and `tests/test_search.py`.
