# Contributing

Any contribution is welcome and we only ask contributors to:

- Create an issue for any significant contribution that would change a large portion of the code base
- Provide at least integration tests for any contribution

## Getting set up

`ansible-test` needs the collection to live at a path ending in
`ansible_collections/cloudscale_ch/cloud`, so clone it directly into that layout:

```
git clone https://github.com/cloudscale-ch/ansible-collection-cloudscale.git \
  ansible_collections/cloudscale_ch/cloud
cd ansible_collections/cloudscale_ch/cloud
```

Create a virtual environment and install `ansible-core`:

```bash
# or use uv/poetry/pipenv/...
python -m venv .venv
source .venv/bin/activate

# install ansible-core
pip install ansible-core
```

The tests use Docker for isolation (`--docker`), so a working Docker install is the only other
requirement.

## Running tests

Sanity tests:

```
ansible-test sanity --docker --python 3.12
```

Unit tests:

```
ansible-test units --docker --python 3.12
```

Integration tests need a cloudscale.ch API token. Copy the template and replace
`@API_TOKEN` with your token:

```
cp tests/integration/cloud-config-cloudscale.ini.template tests/integration/cloud-config-cloudscale.ini
```

Then run a single target, for example:

```
ansible-test integration --docker --python 3.12 server --allow-unsupported
```

Integration tests create and delete real resources on your cloudscale.ch
account and cost money. The two config files hold real credentials and are
git-ignored.

## Overriding the API URL

To run the integration tests against a non-production API, copy
the second template and set `cloudscale_api_url`:

```
cp tests/integration/integration_config.yml.template tests/integration/integration_config.yml
```

When left unset the tests use production. See the comments in the template for
details.

## Generating documentation

To preview the module documentation locally, use `antsibull-docs`:

```
pip install antsibull-docs
# point antsibull-docs at the directory that contains ansible_collections/
export ANSIBLE_COLLECTIONS_PATH="$(cd ../../.. && pwd)"

# create target dir and ensure correct permissions
mkdir /tmp/cloudscale-docs
chmod 755 /tmp/cloudscale-docs

# generate docs base
antsibull-docs sphinx-init --use-current --dest-dir /tmp/cloudscale-docs cloudscale_ch.cloud
cd /tmp/cloudscale-docs

# generate documentation - ensure you're in a venv
pip install -r requirements.txt
# in case you created a new venv, ansible-core needs to be installed additionally
pip install ansible-core
# build docs
./build.sh
```

Then open `build/html/index.html`.
