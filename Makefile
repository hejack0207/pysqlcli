.PHONY: build

gen-requirements:
	pipreqs . --print

build:
	python setup.py build
