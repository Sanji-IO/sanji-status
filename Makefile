PROJECT=sanji-bundle-status
VERSION=$(shell cat bundle.json | sed -n 's/"version"//p' | tr -d '", :')

ARCHIVE=$(CURDIR)/$(PROJECT)_$(VERSION).tar.gz

SANJI_VER=1.0

INSTALL_DIR=$(DESTDIR)/usr/lib/sanji-$(SANJI_VER)/$(PROJECT)

STAGING_DIR=$(CURDIR)/staging

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

STAGING_FILES=$(addprefix $(STAGING_DIR)/$(PROJECT)/,$(FILES))

.PHONY: clean dist pylint test

all:

clean:
	rm -rf $(PROJECT)_*.tar.gz $(STAGING_DIR)

dist: $(ARCHIVE)

pylint:
	flake8 --exclude=tests,.git,env,.env -v .

test:
	nosetests --with-coverage --cover-erase --cover-package=sanji_status

$(ARCHIVE): $(STAGING_FILES)
	cd $(STAGING_DIR) && \
	tar zcf $@ $(PROJECT)

$(STAGING_DIR)/$(PROJECT)/%: %
	mkdir -p $(dir $@)
	cp -a $< $@

install: $(INSTALL_FILES)

$(INSTALL_DIR)/%: %
	mkdir -p $(dir $@)
	install $< $@

uninstall:
	-rm $(addprefix $(INSTALL_DIR)/,$(FILES))
