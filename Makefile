help:
	@echo 'No build is required.  See README.md'

all: test gcode_dryrun dryrun lint

test:
	python2 fygen_test.py
	python3 fygen_test.py

lint:
	PYTHONPATH=$(shell pwd) pylint \
   *.py \
   examples/basic/*.py \
   examples/modulation/*.py \
   examples/arb/*.py \
   examples/gcode/*.py \
   examples/sweep/*.py

GCD_FILES:=$(wildcard examples/gcode/*.gcd)
.PHONY: $(GCD_FILES)

$(GCD_FILES):
	cd examples/gcode && ./xy_gcode_plot.py ../../$@ --dry_run > /dev/null

gcode_dryrun: $(GCD_FILES)

dryrun:
	cd examples/basic && ./all_waves.py --dry_run --test_mode > /dev/null

clean:
	rm -rf __pycache__
	rm -rf $(shell find . -name '*.pyc')
