PROJ_DIR=$(abspath ..)
PROJECT=sanji-bundle-status
VERSION=$(shell cat $(PROJ_DIR)/bundle.json | sed -n 's/"version"//p' | tr -d '", :')
DEBVERSION=2

STAGING_DIR=$(abspath staging)

UPSTREAM_ARCHIVE=$(PROJECT)_$(VERSION).tar.gz

FILES= \
	$(STAGING_DIR)/debian/changelog \
	$(STAGING_DIR)/debian/compat \
	$(STAGING_DIR)/debian/control \
	$(STAGING_DIR)/debian/copyright \
	$(STAGING_DIR)/debian/docs \
	$(STAGING_DIR)/debian/postinst \
	$(STAGING_DIR)/debian/README \
	$(STAGING_DIR)/debian/rules \
	$(STAGING_DIR)/debian/source/format

.PHONY: all build

all: build

build: extract-upstream $(FILES)
	cd $(STAGING_DIR) && \
	dpkg-buildpackage -us -uc -rfakeroot

$(STAGING_DIR)/debian/%: $(PROJ_DIR)/build-deb/debian/%
	mkdir -p $(dir $@)
	cp $< $@

extract-upstream:
	mkdir -p $(STAGING_DIR)
	cd $(STAGING_DIR) && \
	tar zxf $(PROJ_DIR)/$(UPSTREAM_ARCHIVE)

changelog:
	dch -v $(VERSION)-$(DEBVERSION) -M -u low --release-heuristic log

clean:
	rm -rf $(STAGING_DIR) $(PROJECT)_*
