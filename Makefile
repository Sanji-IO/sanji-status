PROJECT=sanji-bundle-status
VERSION=$(shell cat bundle.json | sed -n 's/"version"//p' | tr -d '", :')

ARCHIVE=$(abspath $(PROJECT)_$(VERSION).tar.gz)

SANJI_VER=1.0
INSTALL_DIR=$(DESTDIR)/usr/lib/sanji-$(SANJI_VER)/$(PROJECT)

FILES= \
	bundle.json \
	Makefile \
	README.md \
	requirements.txt \
	status.py \
	data/status.json.factory \
	sanji_status/dao.py \
	sanji_status/flock.py \
	sanji_status/__init__.py \
	sanji_status/monitor.py

INSTALL_FILES=$(addprefix $(INSTALL_DIR)/,$(FILES))

.PHONY: pylint test build

all:

clean:
	rm -rf $(PROJECT)_*.tar.gz

pylint:
	flake8 --exclude=tests,.git,env,.env -v .

test:
	nosetests --with-coverage --cover-erase --cover-package=sanji_status

archive: $(ARCHIVE)

$(ARCHIVE): $(FILES)
	tar zcf $@ $(FILES)

install: $(INSTALL_FILES)

$(INSTALL_DIR)/%: %
	mkdir -p $(dir $@)
	install $< $@

uninstall:
	-rm $(addprefix $(INSTALL_DIR)/,$(FILES))
