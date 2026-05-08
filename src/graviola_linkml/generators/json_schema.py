"""GraviolaJsonSchemaGenerator — subclasses the upstream LinkML JsonSchemaGenerator.

Key differences from the upstream output:
- Uses `definitions` (draft-07 style) instead of `$defs`
- `$ref` paths use `#/definitions/` prefix
- Injects `@id: {type: string}` and `@type: {type: string, const: <IRI>}` into every class
- Injects `x-inverseOf` extension on multivalued slots that declare `inverse`
- No nullable union types (`include_null` defaults to False)
- No `$schema`, `$id`, `title`, `additionalProperties` at the top level
- Property names and class names preserved as-is (`preserve_names` defaults to True)
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from linkml.generators.common.build import ClassResult, SlotResult
from linkml.generators.jsonschemagen import JsonSchema, JsonSchemaGenerator
from linkml_runtime.linkml_model.meta import ClassDefinition, SlotDefinition
from linkml_runtime.utils.formatutils import camelcase


@dataclass
class GraviolaJsonSchemaGenerator(JsonSchemaGenerator):
    """Generates Graviola-flavoured JSON Schema from a LinkML SchemaDefinition."""

    # Keep slot/class names exactly as written in the LinkML YAML (camelCase etc.)
    preserve_names: bool = True
    # Do not emit nullable union types for optional slots
    include_null: bool = False

    # ------------------------------------------------------------------ #
    # Lifecycle overrides                                                  #
    # ------------------------------------------------------------------ #

    def start_schema(self, inline: bool = False) -> None:
        """Create a minimal top-level schema — no $schema/$id/title headers."""
        self.inline = inline
        self.top_level_schema = JsonSchema({"type": "object"})

    def after_generate_class(
        self,
        result: ClassResult,
        schemaview,
    ) -> ClassResult:
        """Inject @id / @type and strip noise fields added by the parent."""
        cls: ClassDefinition = result.source
        class_uri = self._resolve_class_uri(cls, schemaview)

        result.schema_.pop("additionalProperties", None)
        desc = result.schema_.pop("description", "")
        if desc:
            result.schema_["description"] = desc

        existing_props = result.schema_.pop("properties", {})
        result.schema_["properties"] = {
            "@id": {"type": "string"},
            "@type": {"type": "string", "const": class_uri},
            **existing_props,
        }
        return result

    def after_generate_class_slot(
        self,
        result: SlotResult,
        cls: ClassDefinition,
        schemaview,
    ) -> SlotResult:
        """Inject x-inverseOf on multivalued slots that declare an inverse."""
        slot: SlotDefinition = result.source
        inverse = getattr(slot, "inverse", None)
        if inverse and result.schema_.is_array:
            range_name = getattr(slot, "range", None)
            if range_name and schemaview.get_class(str(range_name)):
                owner_class = camelcase(str(range_name))
                result.schema_["x-inverseOf"] = {
                    "inverseOf": [
                        f"#/definitions/{owner_class}/properties/{inverse}"
                    ]
                }
        return result

    # ------------------------------------------------------------------ #
    # Serialization — post-process the upstream JSON                       #
    # ------------------------------------------------------------------ #

    def serialize(self, **kwargs) -> str:  # type: ignore[override]
        raw = super().serialize(**kwargs)
        return self._to_graviola(raw)

    def _to_graviola(self, json_str: str) -> str:
        data = json.loads(json_str)

        # Rename $defs -> definitions (draft-07 style)
        if "$defs" in data:
            data["definitions"] = data.pop("$defs")

        # Remove top-level meta-headers that Graviola consumers don't use
        for key in (
            "$schema",
            "$id",
            "metamodel_version",
            "version",
            "title",
            "additionalProperties",
            "description",
        ):
            data.pop(key, None)

        # Rewrite all $ref paths: #/$defs/ -> #/definitions/
        _fix_refs(data)

        # Strip per-class noise fields added by add_def / handle_class
        for defn in data.get("definitions", {}).values():
            defn.pop("title", None)

        indent = self.indent if self.indent > 0 else None
        return json.dumps(data, indent=indent) + "\n"

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _resolve_class_uri(self, cls: ClassDefinition, schemaview) -> str:
        """Expand a class_uri CURIE to a full IRI using the schema's prefix map."""
        raw = str(cls.class_uri) if cls.class_uri else None
        if not raw:
            return f"{schemaview.schema.id}{cls.name}"
        if ":" in raw:
            prefix, local = raw.split(":", 1)
            prefixes = schemaview.schema.prefixes
            if prefix in prefixes:
                ref = str(prefixes[prefix].prefix_reference)
                return f"{ref}{local}"
        return raw


# ------------------------------------------------------------------ #
# Module-level helpers                                                #
# ------------------------------------------------------------------ #


def _fix_refs(obj: object) -> None:
    """Recursively rewrite '#/$defs/' to '#/definitions/' in all $ref strings."""
    if isinstance(obj, dict):
        if "$ref" in obj and isinstance(obj["$ref"], str):
            obj["$ref"] = obj["$ref"].replace("#/$defs/", "#/definitions/")
        for v in obj.values():
            _fix_refs(v)
    elif isinstance(obj, list):
        for item in obj:
            _fix_refs(item)
