# PyGrobid

A python version of GROBID (proof-of-concept).
This currently only supports Linux.

## Development

### Create Virtual Environment and install Dependencies

```bash
make dev-venv
```

### Configuration

There is no implicit "grobid-home" directory. The only configuration file is [config.yml](config.yml).

Paths may point to local or remote files. Remote files are downloaded and cached locally (urls are assumed to be versioned).

### Run tests (linting, pytest, etc.)

```bash
make dev-test
```

### Start the server

```bash
make dev-start
```

### Submit a sample document to the server

```bash
curl --fail --show-error \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/pdfalto"
```

### Submit a sample document to the header model

The following output formats are supported:

| output_format | description |
| ------------- | ----- |
| raw_data | generated data (without using the model) |
| data | generated data with predicted labels |
| xml | using simple xml elements for predicted labels |
| json | json of prediction |

```bash
curl --fail --show-error \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/models/header?first_page=1&last_page=1&output_format=xml"
```

### Submit a sample document to the full text api

```bash
curl --fail --show-error \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/processFulltextDocument?first_page=1&last_page=1"
```

### Docker Usage

```bash
docker pull de4code/pygrobid-poc_unstable
```

```bash
docker run --rm \
    -p 8070:8070 \
    de4code/pygrobid-poc_unstable
```
