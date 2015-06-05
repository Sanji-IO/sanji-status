
include debian.conf

# Where to put executable commands/icons/conf on 'make install'?
LIBDIR      = $(DESTDIR)/usr/lib/sanji-$(SANJI_VER)/$(NAME)
TMPDIR      = $(DESTDIR)/tmp

FILES       := $(filter-out README.md requirements.txt,$(FILES))


all: $(CURDIR)/packages/bundle-requirements.txt
	# do nothing

$(CURDIR)/packages/bundle-requirements.txt:
	mkdir -p $(CURDIR)/packages
	pip install -r $(CURDIR)/requirements.txt --download \
		$(CURDIR)/packages || true
	cp -a $(CURDIR)/requirements.txt \
		$(CURDIR)/packages/bundle-requirements.txt

clean:
	# do nothing

distclean: clean


install: all
	install -d $(LIBDIR)
	install -d $(TMPDIR)
	install $(FILES) $(LIBDIR)
	cp -a $(DIRS) $(LIBDIR)
	cp -a packages $(TMPDIR)

uninstall:
	-rm $(addprefix $(LIBDIR)/,$(FILES))
