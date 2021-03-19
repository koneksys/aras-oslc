.DEFAULT_TARGET   = all
MAKE              := $(MAKE) --no-print-directory
PYTHON            ?= python3
python            := env/bin/python
pip               := env/bin/pip
twine             := env/bin/twine
pip_find_index    ?=
pip_upload_url    ?=
user              ?=
token             ?=
quiet             ?=
python_wheel_spec ?= bdist_wheel
redirect_io       ?= #> /dev/null
requirements      := requirements.txt dev-require.txt
setup_tools       := setuptools pip-tools wheel
clean_objects     := env dist $(requirements) build *.egg-info
wheel_target      := ./dist/*.whl
env_target        := ./env
pip_install       := env/bin/pip install $(quiet) --progress-bar off $(pip_find_index)
pip_compile       := env/bin/pip-compile $(quiet) $(pip_find_index)
pip_wheel         := env/bin/pip wheel $(quiet) --progress-bar off $(pip_find_index)
linting_dirs      ?= .
formatting_dirs   ?= .
testing_dirs      ?= .
tmp_dir           := $(shell bash -c 'echo tmp$$$$$$$$')

.PHONY: all

all: $(env_target) wheel

clean:
	@rm -rf $(clean_objects)

virtual-env: $(env_target)

update: $(requirements)
	@echo "**** make install --editable ****"
	$(pip_install) --editable .

commitno:
	@echo "**** generate COMMITNO based on git count ****"
	git rev-list --count --first-parent HEAD > COMMITNO

wheel: $(wheel_target)

wheel-house: wheel
	@echo "**** export wheels ****"
	mkdir $(tmp_dir)
	$(pip_wheel) --wheel-dir=$(tmp_dir) $(wheelpath)
	cp -f $(tmp_dir)/*.whl $(outpath)
	rm -rf $(tmp_dir)

publish: $(requirements)
	@echo "**** publish to artifact repo ****"
	$(twine) upload --disable-progress-bar --repository-url $(pip_upload_url) --skip-existing --verbose --username $(user) --password $(token) dist/*.whl

requirements.txt: setup.py
	@echo "**** compile and install module requirements ****"
	$(pip_compile) --generate-hashes --upgrade
	$(pip_install) --upgrade -r requirements.txt

dev-require.txt: dev-require.in
	@echo "**** compile and install development requirements ****"
	$(pip_compile) --upgrade --output-file dev-require.txt dev-require.in
	$(pip_install) --upgrade -r dev-require.txt

$(env_target):
	@echo "**** make virtual environment ****"
	$(PYTHON) -m venv env
	$(pip) install $(quiet) --upgrade pip
	$(pip_install) --upgrade $(setup_tools)
	@echo "ok, now run this: source env/bin/activate"

$(wheel_target): $(requirements)
	@echo "**** compile wheel file ****"
	@rm -rf $(wheel_target)
	$(python) setup.py $(python_wheel_spec) $(redirect_io)
