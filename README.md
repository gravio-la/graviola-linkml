# graviola-linkml

Generate Graviola-ready artifacts from LinkML schemas.

The CLI creates:

- `<schema-stem>.schema.json` (Graviola JSON Schema)
- `<schema-stem>.gra.side-schema.json` (Graviola side-schema with labels, primary fields, UI hints)

## Worked Example (contract style)

The example contract is committed in `examples/collective-mind-schema.yml`.
It includes:

- relations with inverse declarations (`memberOf` <-> `members`, `hostBody` <-> `hostedMinds`)
- `gra:` namespace annotations (`gra:label`, `gra:primaryLabel`)

Generate the outputs exactly as documented:

```bash
nix run .#generate -- ./examples/collective-mind-schema.yml -o ./examples/collective-mind.schema.json
nix run .#side-schema -- ./examples/collective-mind-schema.yml -o ./examples/collective-mind.gra.side-schema.json
```

Source excerpt (`examples/collective-mind-schema.yml`):

```yaml
classes:
  Individual:
    annotations:
      gra:label: "Individual Being"
      gra:primaryLabel: name
    slots: [name, embodiedMind, memberOf]
  Collective:
    annotations:
      gra:label: "Collective"
      gra:primaryLabel: title
    slots: [title, members]
slots:
  memberOf:
    range: Collective
    inlined: true
    inverse: members
  members:
    range: Individual
    multivalued: true
    inlined: true
```

Generated excerpt (`examples/collective-mind.schema.json`):

```json
{
  "definitions": {
    "Collective": {
      "properties": {
        "members": {
          "items": { "$ref": "#/definitions/Individual" },
          "type": "array"
        },
        "title": { "type": "string" }
      }
    },
    "Individual": {
      "properties": {
        "memberOf": { "$ref": "#/definitions/Collective" },
        "name": { "type": "string" }
      }
    }
  }
}
```

Generated excerpt (`examples/collective-mind.gra.side-schema.json`):

```json
{
  "primaryFields": {
    "Individual": { "label": "name" },
    "Collective": { "label": "title" }
  },
  "typeNameLabelMap": {
    "Individual": "Individual Being",
    "Collective": "Collective"
  }
}
```

## Run

### Nix (no install)

From this repo:

```bash
nix run .#generate -- ./examples/collective-mind-schema.yml
nix run .#side-schema -- ./examples/collective-mind-schema.yml
```

From GitHub:

```bash
nix run github:graviola-la/graviola-linkml#generate -- ./model.yaml -o ./model.schema.json
nix run github:graviola-la/graviola-linkml#side-schema -- ./model.yaml -o ./model.gra.side-schema.json
```

Full CLI help:

```bash
nix run . -- --help
```

### Python / uv

```bash
uv sync
uv run graviola-linkml --help
uv run graviola-linkml generate ./examples/collective-mind-schema.yml
uv run graviola-linkml side-schema ./examples/collective-mind-schema.yml
```

## CLI

- `generate <schema.yaml>`
  - `-o, --output <path>` (default: `<schema-stem>.schema.json`)
  - `--indent <n>` (default: `2`)
- `side-schema <schema.yaml>`
  - `-o, --output <path>` (default: `<schema-stem>.gra.side-schema.json`)

## Nix Dev Shell

```bash
nix develop
```

Inside the shell, `graviola-linkml`, `uv`, and `ruff` are available.

## Local Development

```bash
uv sync --extra dev
uv run pytest -v
uv run ruff check .
uv run mypy src
```

## Annotation Vocabulary Publishing

`.github/workflows/publish-schema.yml` builds and deploys artifacts from `annotation-vocab/graviola-annotations.yaml`:

- Turtle (`.ttl`)
- JSON-LD (`.jsonld`)
- HTML docs (MkDocs)
- source YAML + `.htaccess`

