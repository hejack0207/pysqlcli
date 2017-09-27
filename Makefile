gen-requirements:
	pipreqs . --print

.PHONY: build
build:
	python setup.py build
