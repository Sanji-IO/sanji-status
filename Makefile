all: pylint test

pylint:
	flake8 --exclude=tests,.git,env -v .
test:
	nosetests --with-coverage --cover-erase --cover-package=status

.PHONY: pylint test
