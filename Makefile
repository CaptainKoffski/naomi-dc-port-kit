.DEFAULT_GOAL := test
.PHONY: test
test:
	python3 scripts/test_kitpath.py
	mkdir -p build
	cc -o build/test_naomi_crc shims/test/test_naomi_crc.c loader/naomi_crc.c && build/test_naomi_crc
	python3 scripts/test_apply_reloc.py
	python3 scripts/test_patchgen.py
	python3 scripts/test_eeprom_game_diff.py
	python3 scripts/test_gdemu_deploy.py
