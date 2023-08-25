clean:
	rm -fr .direnv

env:
	# CFLAGS="$(pkg-config --cflags libffi)" \
	# LDFLAGS="$(pkg-config --libs libffi) $(pkg-config --libs libssl)" \
	pyenv install; \
	direnv allow

install:
	pip install --upgrade pip; \
	pip install poetry; \
	poetry install

lint:
	# black --exclude=".direnv/*" .
	flake8 --exclude=".direnv/*" .
