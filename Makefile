all: pylint test

pylint:
	flake8 --exclude=tests,.git,env,.env -v .

test:
	nosetests --with-coverage --cover-erase --cover-package=sanji_status

.PHONY: pylint test
include make.deb
