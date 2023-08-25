clean:
	rm -fr .direnv

env:
	# CFLAGS="$(pkg-config --cflags libffi)" \
	# LDFLAGS="$(pkg-config --libs libffi) $(pkg-config --libs libssl)" \
	pyenv install; \
	direnv allow

install:
	# Installing `urllib3==1.26.6` is required to clear the error:
	# ImportError: urllib3 v2.0 only supports OpenSSL 1.1.1+, currently
	# the 'ssl' module is compiled with 'OpenSSL 1.0.2k-fips.
	# Ref: https://stackoverflow.com/questions/76187256/importerror-urllib3-v2-0-only-supports-openssl-1-1-1-currently-the-ssl-modu
	pip install --upgrade pip; \
	pip install urllib3==1.26.6 \
	pip install poetry; \
	poetry install

lint:
	# black --exclude=".direnv/*" .
	flake8 --exclude=".direnv/*" .
