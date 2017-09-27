.PHONY: build

gen-requirements:
	pipreqs . --print

build:
	python setup.py clean build

install:
	sudo python setup.py install

clean:
	sudo rm -rf build dist
