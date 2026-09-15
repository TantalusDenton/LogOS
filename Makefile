SHELL := /bin/bash
.PHONY: all check sources lfs blfs x11 ai image import create start stop shell status health test clean
all:
	./build/build-logos.sh --resume
check:
	./build/check-host.sh
sources:
	./build/download-sources.sh
lfs:
	./build/build-lfs.sh
blfs:
	./build/build-blfs.sh
x11:
	./build/build-x11.sh
ai:
	./build/build-ai.sh
image:
	./build/package-rootfs.sh
import:
	./host/import-image.sh
create:
	./host/create-container.sh
start:
	./host/start-logos.sh
stop:
	./host/stop-logos.sh
shell:
	./host/shell.sh
status:
	./host/status.sh
health:
	./host/health.sh
test:
	PYTHONPATH=logos-ai /usr/bin/python3 -m unittest discover -s logos-ai/tests -v
	/usr/bin/python3 -m unittest discover -s tests -v
	find build host rootfs-overlay -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n
	bash -n rootfs-overlay/usr/bin/logos-session
clean:
	./build/clean.sh --work-only
