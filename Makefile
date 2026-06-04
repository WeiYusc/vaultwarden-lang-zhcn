.PHONY: check check-upstream package smoke clean

PYTHON ?= python3

check-upstream:
	$(PYTHON) scripts/check_upstream_manifest.py

check: check-upstream
	$(PYTHON) scripts/check_file_list.py
	$(PYTHON) scripts/check_tokens.py
	$(PYTHON) scripts/check_email_delimiters.py

package: check
	$(PYTHON) scripts/build_release.py

smoke:
	scripts/smoke_vaultwarden_container.sh

clean:
	rm -rf dist
