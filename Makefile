clean:
	rm -fr .direnv

env:
	pyenv install; \
	direnv allow

install:
	pip install --upgrade pip; \
	pip install poetry; \
	poetry install

lint:
	# black --exclude=".direnv/*" .
	flake8 --exclude=".direnv/*" .
