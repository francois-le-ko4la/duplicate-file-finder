# Makefile

PACKAGE_NAME = "duplicatefile"
PACKAGE_DIR = $(PACKAGE_NAME)
MAKE := $(MAKE) --no-print-directory
SHELL = bash

default:
	@echo "Makefile for $(PACKAGE_NAME)"
	@echo
	@echo 'Usage:'
	@echo
	@echo '    user : make install                   install the packages'
	@echo '           make uninstall                 remove the package'
	@echo '    dev  : make venv                      install venv'
	@echo '           source venv/bin/activate       activate venv'
	@echo '           make dev                       install dev packages'
	@echo '           make test                      test'
	@echo '           make doc                       update uml'
	@echo

install:
	@pip3 install . --user

uninstall:
	pip3 uninstall -y $(PACKAGE_NAME)

venv:
	@pip3 install virtualenv --user
	@virtualenv venv

dev:
	@pip3 install -e ".[dev]"

test:
	@pytest --pyargs $(PACKAGE_NAME)

doc:
	@pyreverse -ASmy -o mmd src/$(PACKAGE_DIR)/$(PACKAGE_NAME).py -d doc

docstring2md:
	@export_docstring2md -p $(PACKAGE_DIR) --output-file README.md -mmd doc/classes.mmd -tml pyproject.toml --toc

publish:
	@pytest --pyargs $(PACKAGE_NAME)
	@git add .
	@git commit
	@git push

.PHONY: default install uninstall dev test doc publish
