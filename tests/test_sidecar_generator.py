"""Tests for GraviolaSidecarGenerator against item_schema_annotated.yaml fixture."""

import json
from functools import lru_cache
from pathlib import Path

import pytest

from graviola_linkml.generators.side_schema import GraviolaSideSchemaGenerator

FIXTURE = Path(__file__).parent / "fixtures" / "item_schema_annotated.yaml"


@lru_cache(maxsize=1)
def _sidecar() -> dict:
    gen = GraviolaSideSchemaGenerator(str(FIXTURE))
    return json.loads(gen.serialize())


# ------------------------------------------------------------------ #
# primaryFields                                                        #
# ------------------------------------------------------------------ #


def test_primary_fields_category_label():
    assert _sidecar()["primaryFields"]["Category"]["label"] == "name"


def test_primary_fields_category_description():
    assert _sidecar()["primaryFields"]["Category"]["description"] == "description"


def test_primary_fields_category_image():
    assert _sidecar()["primaryFields"]["Category"]["image"] == "image"


def test_primary_fields_item_image():
    assert _sidecar()["primaryFields"]["Item"]["image"] == "photos"


def test_primary_fields_vendor_image():
    assert _sidecar()["primaryFields"]["Vendor"]["image"] == "logo"


def test_primary_fields_all_classes_present():
    pf = _sidecar()["primaryFields"]
    assert {"Category", "Item", "Tag", "Vendor"} <= pf.keys()


# ------------------------------------------------------------------ #
# typeNameLabelMap                                                     #
# ------------------------------------------------------------------ #


def test_label_map_category():
    assert _sidecar()["typeNameLabelMap"]["Category"] == "Kategorie"


def test_label_map_item():
    assert _sidecar()["typeNameLabelMap"]["Item"] == "Artikel"


def test_label_map_tag():
    assert _sidecar()["typeNameLabelMap"]["Tag"] == "Tag"


def test_label_map_vendor():
    assert _sidecar()["typeNameLabelMap"]["Vendor"] == "Lieferant"


# ------------------------------------------------------------------ #
# typeNameUiSchemaOptionsMap                                          #
# ------------------------------------------------------------------ #


def test_display_as_category_dropdown():
    assert _sidecar()["typeNameUiSchemaOptionsMap"]["Category"] == {"dropdown": True}


def test_display_as_tag_chips():
    assert _sidecar()["typeNameUiSchemaOptionsMap"]["Tag"] == {"chips": True}


def test_display_as_vendor_dropdown():
    assert _sidecar()["typeNameUiSchemaOptionsMap"]["Vendor"] == {"dropdown": True}


def test_no_display_as_on_item():
    assert "Item" not in _sidecar()["typeNameUiSchemaOptionsMap"]


# ------------------------------------------------------------------ #
# uischemaScopeOverrides (form)                                       #
# ------------------------------------------------------------------ #


def test_form_override_subcategories_control_type():
    scope = "#/properties/subCategories"
    ctrl = _sidecar()["uischemaScopeOverrides"]["Category"]["scopeOverride"][scope]
    assert ctrl["type"] == "Control"
    assert ctrl["scope"] == scope


def test_form_override_subcategories_options():
    scope = "#/properties/subCategories"
    ctrl = _sidecar()["uischemaScopeOverrides"]["Category"]["scopeOverride"][scope]
    assert ctrl["options"]["dropdown"] is True
    assert ctrl["options"]["chips"] is True


def test_form_override_tags_chips():
    scope = "#/properties/tags"
    ctrl = _sidecar()["uischemaScopeOverrides"]["Item"]["scopeOverride"][scope]
    assert ctrl["options"]["chips"] is True
    assert ctrl["options"]["dropdown"] is True


def test_no_form_overrides_for_tag():
    assert "Tag" not in _sidecar().get("uischemaScopeOverrides", {})


def test_no_form_overrides_for_vendor():
    assert "Vendor" not in _sidecar().get("uischemaScopeOverrides", {})


# ------------------------------------------------------------------ #
# detailUiSchemaScopeOverrides                                        #
# ------------------------------------------------------------------ #


def test_detail_skip_photos():
    detail = _sidecar()["detailUiSchemaScopeOverrides"]["Item"]
    assert "#/properties/photos" in detail["skipScope"]


def test_detail_skip_logo():
    detail = _sidecar()["detailUiSchemaScopeOverrides"]["Vendor"]
    assert "#/properties/logo" in detail["skipScope"]


def test_detail_skip_subcategories():
    detail = _sidecar()["detailUiSchemaScopeOverrides"]["Category"]
    assert "#/properties/subCategories" in detail["skipScope"]


def test_detail_label_parent_category():
    scope = "#/properties/parentCategory"
    ctrl = _sidecar()["detailUiSchemaScopeOverrides"]["Category"]["scopeOverride"][scope]
    assert ctrl["label"] == "Übergeordnete Kategorie"
    assert ctrl["type"] == "Control"
    assert ctrl["scope"] == scope


def test_detail_label_baseprice_item():
    scope = "#/properties/basePrice"
    ctrl = _sidecar()["detailUiSchemaScopeOverrides"]["Item"]["scopeOverride"][scope]
    assert ctrl["label"] == "Preis (€)"


def test_detail_label_baseprice_category():
    scope = "#/properties/basePrice"
    ctrl = _sidecar()["detailUiSchemaScopeOverrides"]["Category"]["scopeOverride"][scope]
    assert ctrl["label"] == "Basispreis (€)"


def test_detail_label_is_available():
    scope = "#/properties/isAvailable"
    ctrl = _sidecar()["detailUiSchemaScopeOverrides"]["Item"]["scopeOverride"][scope]
    assert ctrl["label"] == "Verfügbar"


def test_no_detail_overrides_for_tag():
    assert "Tag" not in _sidecar().get("detailUiSchemaScopeOverrides", {})


def test_vendor_detail_only_skip_no_scope_overrides():
    detail = _sidecar()["detailUiSchemaScopeOverrides"]["Vendor"]
    assert "#/properties/logo" in detail["skipScope"]
    assert "scopeOverride" not in detail
