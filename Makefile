# Macros for working with the source code

clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-find . -name '*.pyc' -delete
	-rm -f tests/.coverage

.PHONY: docs
docs: install
	cd docs && make html

build: clean
	python setup.py sdist

install: uninstall build
	pip install -U dist/*.tar.gz

uninstall:
	-pip uninstall -y iiqtools

test: install
	cd tests && nosetests -v --with-coverage --cover-package=iiqtools

lint: install
	pylint iiqtools
