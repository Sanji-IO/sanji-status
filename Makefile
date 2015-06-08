PROJECT=sanji-bundle-status
VERSION=$(shell jq '.version' bundle.json | tr -d "\"")
ARCHIVE=$(abspath $(PROJECT)_$(VERSION).tar.gz)

SANJI_VER=1.0
INSTALL_DIR=$(DESTDIR)/usr/lib/sanji-$(SANJI_VER)/$(PROJECT)

FILES= \
	bundle.json \
	Makefile \
	README.md \
	requirements.txt \
	status.py \
	data/status.json \
	data/status.json.factory \
	sanji_status/dao.py \
	sanji_status/flock.py \
	sanji_status/__init__.py \
	sanji_status/monitor.py

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

install: $(FILES)
	install -d $(INSTALL_DIR)
	install $(FILES) $(INSTALL_DIR)

uninstall:
	-rm $(addprefix $(INSTALL_DIR)/,$(FILES))
