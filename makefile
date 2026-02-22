tech-screen:
	@if [ -z "$(START)" ] || [ -z "$(STOP)" ]; then \
		echo "Error: START and STOP arguments are required"; \
		echo "Usage: make tech-screen START='Park Street' STOP='South Station'"; \
		exit 1; \
	fi
	cd main && python main.py tech-screen --start "$(START)" --stop "$(STOP)"

stops:
	cd main && python main.py list-stops

# Run tests
test:
	python -m pytest tests/unit/ -v

install:
	pip install -r requirements.txt

lint:
	black .

help:
	cd main && python main.py --help