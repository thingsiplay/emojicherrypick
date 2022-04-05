SHELL = /bin/bash

APP_NAME := emojicherrypick
APP_VERSION := $(shell python3 ./$(APP_NAME).py --version | grep -oE '[0-9]+\.[0-9]+')

7Z_PATH := 7z

SRC_DIR := .
DIST_DIR := ./dist
PACKAGE_PATH := $(DIST_DIR)/$(APP_NAME)-$(APP_VERSION)-Linux-bin.zip
VENV_DIR := $(SRC_DIR)/venv_$(APP_NAME)
PYINSTALLER_PATH := $(VENV_DIR)/bin/pyinstaller

.DEFAULT_GOAL := build

build: check venv dist pack

all: clean build install

check:
	test "$(APP_NAME).py"
	which 7z
	python3 --version | grep -E '3.[1-9][0-9]'

install:
	cd "$(DIST_DIR)" \
		&& "./install.sh"

uninstall:
	cd "$(DIST_DIR)" \
		&& "./uninstall.sh"

distclean:
	rm -f "$(DIST_DIR)/"* \
		&& rm -d -f "$(DIST_DIR)"

clean: distclean
	rm -f "$(APP_NAME).spec"
	rm -r -f "__pycache__"
	rm -r -f "./build/$(APP_NAME)" \
		&& rm -d -f "./build"
	rm -f "$(VENV_DIR)/pyenv.cfg" \
		&& rm -r -f "$(VENV_DIR)"

pack: 
	rm -f "$(PACKAGE_PATH)"
	"$(7Z_PATH)" a "$(PACKAGE_PATH)" "$(DIST_DIR)/"*

dist: 
	mkdir -p "$(DIST_DIR)"
	cp "$(SRC_DIR)/LICENSE" "$(DIST_DIR)"
	cp "$(SRC_DIR)/install.sh" "$(DIST_DIR)"
	cp "$(SRC_DIR)/uninstall.sh" "$(DIST_DIR)"
	cp "$(SRC_DIR)/CHANGES.md" "$(DIST_DIR)"
	cp "$(SRC_DIR)/README.md" "$(DIST_DIR)"
	cp "$(SRC_DIR)/default.webp" "$(DIST_DIR)"
	cp "$(SRC_DIR)/bigfavorites.webp" "$(DIST_DIR)"
	source "$(VENV_DIR)/bin/activate" \
		&& "$(PYINSTALLER_PATH)" --onefile --clean --log-level WARN "$(APP_NAME).py"
	chmod +x "$(DIST_DIR)/$(APP_NAME)"
	chmod +x "$(DIST_DIR)/install.sh"
	chmod +x "$(DIST_DIR)/uninstall.sh"

venv:
	python3 -m venv "$(VENV_DIR)" \
		&& source "$(VENV_DIR)/bin/activate" \
		&& pip3 install --upgrade pip \
		&& pip3 install pyinstaller
