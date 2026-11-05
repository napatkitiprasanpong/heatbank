.PHONY: test demo faults export verify check
test:
	python -m unittest discover -s tests -t .
demo:            # TOY model: shows the plumbing, numbers are NOT results
	python -m heatbank.cli plan --scenario hot_humid --toy --archetype A09
faults:
	python -m heatbank.cli faults
export:       # TOY demo pack; drop --toy once pythermalcomfort works
	python -m heatbank.export --toy --out dashboard/data.js

verify:          # everything that can run without the real library: unit tests + page smoke test + toy integration
	python -m unittest discover -s tests -t .
	python scripts/integration_check.py --toy
check:           # on YOUR machine once pythermalcomfort is installed: attach out/check_signatures_output.txt and out/integration_check.txt
	python scripts/check_signatures.py
	python scripts/integration_check.py
