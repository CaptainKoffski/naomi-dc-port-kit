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
	python3 scripts/test_carve_ram_snapshot.py
	python3 scripts/test_check_stream_crc.py
	python3 scripts/test_parse_cartlog.py
	python3 scripts/test_parse_shimtime.py
	python3 scripts/test_scan_dat_constants.py
