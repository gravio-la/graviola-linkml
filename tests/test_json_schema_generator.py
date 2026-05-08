"""Tests for GraviolaJsonSchemaGenerator against the item_schema.yaml fixture.

Validates that the generated JSON Schema matches the Graviola shape
"""

import json
from functools import lru_cache
from pathlib import Path

import pytest

from graviola_linkml.generators.json_schema import GraviolaJsonSchemaGenerator

FIXTURE = Path(__file__).parent / "fixtures" / "item_schema.yaml"


@lru_cache(maxsize=1)
def _generated() -> dict:
    gen = GraviolaJsonSchemaGenerator(str(FIXTURE))
    return json.loads(gen.serialize())


# ------------------------------------------------------------------ #
# Top-level shape                                                      #
# ------------------------------------------------------------------ #


def test_top_level_type():
    assert _generated()["type"] == "object"


def test_uses_definitions_not_defs():
    s = _generated()
    assert "definitions" in s
    assert "$defs" not in s


def test_no_schema_meta_headers():
    s = _generated()
    for key in ("$schema", "$id", "metamodel_version", "title"):
        assert key not in s, f"unexpected top-level key: {key}"


# ------------------------------------------------------------------ #
# Class presence                                                       #
# ------------------------------------------------------------------ #


def test_all_four_classes_present():
    defs = _generated()["definitions"]
    assert {"Category", "Item", "Tag", "Vendor"} <= defs.keys()


# ------------------------------------------------------------------ #
# @id / @type injection                                                #
# ------------------------------------------------------------------ #


@pytest.mark.parametrize(
    "class_name, expected_iri",
    [
        ("Category", "http://www.example.org/example/Category"),
        ("Item",     "http://www.example.org/example/Item"),
        ("Tag",      "http://www.example.org/example/Tag"),
        ("Vendor",   "http://www.example.org/example/Vendor"),
    ],
)
def test_at_id_injected(class_name, expected_iri):
    defn = _generated()["definitions"][class_name]
    assert "@id" in defn["properties"]
    assert defn["properties"]["@id"] == {"type": "string"}


@pytest.mark.parametrize(
    "class_name, expected_iri",
    [
        ("Category", "http://www.example.org/example/Category"),
        ("Item",     "http://www.example.org/example/Item"),
        ("Tag",      "http://www.example.org/example/Tag"),
        ("Vendor",   "http://www.example.org/example/Vendor"),
    ],
)
def test_at_type_const(class_name, expected_iri):
    defn = _generated()["definitions"][class_name]
    at_type = defn["properties"]["@type"]
    assert at_type["type"] == "string"
    assert at_type["const"] == expected_iri


def test_at_id_and_at_type_are_first_properties():
    """@id and @type must be the first two properties in each class."""
    for class_name, defn in _generated()["definitions"].items():
        props = list(defn["properties"].keys())
        assert props[0] == "@id",   f"{class_name}: @id not first"
        assert props[1] == "@type", f"{class_name}: @type not second"


# ------------------------------------------------------------------ #
# required                                                             #
# ------------------------------------------------------------------ #


def test_category_name_required():
    cat = _generated()["definitions"]["Category"]
    assert "name" in cat.get("required", [])


def test_vendor_name_required():
    vendor = _generated()["definitions"]["Vendor"]
    assert "name" in vendor.get("required", [])


# ------------------------------------------------------------------ #
# Scalar properties                                                    #
# ------------------------------------------------------------------ #


def test_string_property():
    cat = _generated()["definitions"]["Category"]
    assert cat["properties"]["name"]["type"] == "string"


def test_integer_property():
    cat = _generated()["definitions"]["Category"]
    assert cat["properties"]["basePrice"]["type"] == "integer"


def test_boolean_property():
    item = _generated()["definitions"]["Item"]
    assert item["properties"]["isAvailable"]["type"] == "boolean"


# ------------------------------------------------------------------ #
# $ref (non-multivalued class reference)                               #
# ------------------------------------------------------------------ #


def test_ref_uses_definitions_prefix():
    cat = _generated()["definitions"]["Category"]
    assert cat["properties"]["parentCategory"]["$ref"] == "#/definitions/Category"


def test_category_ref_on_item():
    item = _generated()["definitions"]["Item"]
    assert item["properties"]["category"]["$ref"] == "#/definitions/Category"


def test_vendor_ref_on_item():
    item = _generated()["definitions"]["Item"]
    assert item["properties"]["vendor"]["$ref"] == "#/definitions/Vendor"


# ------------------------------------------------------------------ #
# Arrays of $ref (multivalued class reference)                         #
# ------------------------------------------------------------------ #


def test_subcategories_is_array_of_category_refs():
    cat = _generated()["definitions"]["Category"]
    sub = cat["properties"]["subCategories"]
    assert sub["type"] == "array"
    assert sub["items"]["$ref"] == "#/definitions/Category"


def test_tags_is_array_of_tag_refs():
    item = _generated()["definitions"]["Item"]
    tags = item["properties"]["tags"]
    assert tags["type"] == "array"
    assert tags["items"]["$ref"] == "#/definitions/Tag"


def test_photos_is_array_of_strings():
    item = _generated()["definitions"]["Item"]
    photos = item["properties"]["photos"]
    assert photos["type"] == "array"
    assert photos["items"]["type"] == "string"


# ------------------------------------------------------------------ #
# x-inverseOf                                                          #
# ------------------------------------------------------------------ #


def test_x_inverse_of_on_subcategories():
    sub = _generated()["definitions"]["Category"]["properties"]["subCategories"]
    assert "x-inverseOf" in sub, "x-inverseOf missing from subCategories"
    assert sub["x-inverseOf"] == {
        "inverseOf": ["#/definitions/Category/properties/parentCategory"]
    }


def test_no_x_inverse_of_on_non_inverse_slots():
    tags = _generated()["definitions"]["Item"]["properties"]["tags"]
    assert "x-inverseOf" not in tags


# ------------------------------------------------------------------ #
# No nullable unions                                                   #
# ------------------------------------------------------------------ #


def test_no_nullable_union_types():
    """No property should have a list type that includes null."""
    defs = _generated()["definitions"]
    for class_name, defn in defs.items():
        for prop_name, prop_schema in defn.get("properties", {}).items():
            typ = prop_schema.get("type")
            if isinstance(typ, list):
                assert "null" not in typ, (
                    f"{class_name}.{prop_name} has a nullable type: {typ}"
                )
