default:
	@echo "'make ui'" to compile ui templates to py modules

PYUIC = python -m PyQt5.uic.pyuic
UI_DIR = templates
PY_DIR = hcibench/templates
UI_TEMPLATES = $(wildcard $(UI_DIR)/*.ui)
PY_TEMPLATES = $(patsubst $(UI_DIR)/%.ui,$(PY_DIR)/%.py,$(UI_TEMPLATES))

.PHONY: ui
ui: $(PY_TEMPLATES)

$(PY_DIR)/%.py: $(UI_DIR)/%.ui
	$(PYUIC) $^ -o $@
