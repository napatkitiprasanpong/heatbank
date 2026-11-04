.PHONY: test demo faults export
test:
	python -m unittest discover -s tests -t .
demo:            # TOY model: shows the plumbing, numbers are NOT results
	python -m heatbank.cli plan --scenario hot_humid --toy --archetype A09
faults:
	python -m heatbank.cli faults
export:       # TOY demo pack; drop --toy once pythermalcomfort works
	python -m heatbank.export --toy --out dashboard/data.js
