#!/usr/bin/make -f

MODULES = \
	vmmon \
	vmnet

all: $(foreach m, $(MODULES), $m.ko)

%.ko: %
	$(MAKE) KVERSION=$(KVERSION) VM_KBUILD=yes EXTRA_CFLAGS="$(EXTRA_CFLAGS)" -C $*-only

$(MODULES): %:
	cp -r $(SRCDIR)/$*-only $*-only

clean:
	rm -rf $(MODULES)
	rm -rf $(foreach m, $(MODULES), $m-only)
	rm -f  $(foreach m, $(MODULES), $m.ko)
	rm -f  $(foreach m, $(MODULES), $m.o)
