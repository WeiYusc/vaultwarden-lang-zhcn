.PHONY: test check check-upstream package package-check smoke clean

PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests -v

check-upstream:
	$(PYTHON) scripts/check_upstream_manifest.py

check: check-upstream
	$(PYTHON) scripts/check_file_list.py
	$(PYTHON) scripts/check_tokens.py
	$(PYTHON) scripts/check_email_delimiters.py
	$(PYTHON) scripts/check_structure_attrs.py
	$(PYTHON) scripts/check_release_target.py
	$(PYTHON) scripts/check_unchanged_translations.py

package: check
	$(PYTHON) scripts/build_release.py

package-check: package
	$(PYTHON) scripts/check_release_archives.py

smoke:
	scripts/smoke_vaultwarden_container.sh

clean:
	rm -rf dist
