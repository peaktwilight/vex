.PHONY: test test-vex test-runtime test-runtime-python test-runtime-rust

test: test-vex test-runtime

test-vex:
	PYTHONPATH=src python3 -m unittest discover -s tests

test-runtime: test-runtime-python test-runtime-rust

test-runtime-python:
	python3 -m unittest discover -s engine/vex-ai-runtime/tests

test-runtime-rust:
	cargo test --manifest-path engine/vex-ai-runtime/Cargo.toml
