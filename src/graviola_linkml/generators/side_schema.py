"""GraviolaSideSchemaGenerator — reads gra: annotations from a LinkML schema and
emits a JSON side-schema file consumed by the TypeScript makeSchemaConfig() call.

Annotation vocabulary (class-level):
  gra:label           → typeNameLabelMap[ClassName]
  gra:displayAs       → typeNameUiSchemaOptionsMap[ClassName] ("dropdown"|"chips")
  gra:primaryLabel    → primaryFields[ClassName].label   (slot name)
  gra:primaryDescription → primaryFields[ClassName].description
  gra:primaryImage    → primaryFields[ClassName].image

Slot-level (in slot_usage, use explicit "value:" key for structured values):
  gra:form   value: {options: {dropdown, chips, …}, label: …}
             → uischemaScopeOverrides[Class].scopeOverride[#/properties/slot]
  gra:detail value: {skip: true, label: "…"}
             → detailUiSchemaScopeOverrides[Class].{skipScope, scopeOverride}

Prefix declaration in LinkML YAML:
  prefixes:
    gra: https://graviola.gra.one/schema/
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from jsonasobj2 import JsonObj
from linkml.utils.generator import Generator
from linkml_runtime.utils.schemaview import SchemaView


def _to_native(obj: Any) -> Any:
    """Recursively convert JsonObj / extended_str to plain Python dicts/strings."""
    if isinstance(obj, JsonObj):
        return {k: _to_native(v) for k, v in vars(obj).items() if k != "_if_missing"}
    if isinstance(obj, list):
        return [_to_native(i) for i in obj]
    # extended_str is a str subclass — return as plain str so JSON is clean
    if type(obj) is not str and isinstance(obj, str):
        return str(obj)
    return obj


def _get_ann(element: Any, tag: str) -> Any | None:
    """Return the Python-native value of annotation *tag* on *element*, or None."""
    ann = element.annotations.get(tag)
    if ann is None:
        return None
    return _to_native(ann.value)


@dataclass
class GraviolaSideSchemaGenerator(Generator):
    """Reads gra: annotations from a LinkML schema and emits a JSON side-schema."""

    generatorname = "graviola-side-schema"
    valid_formats = ["json"]

    # dataclass field to silence the abstract Generator requirement
    format: str = field(default="json", init=False)

    def serialize(self, **kwargs) -> str:  # type: ignore[override]
        sv = SchemaView(self.schema)
        out: dict[str, Any] = {}

        primary = self._primary_fields(sv)
        label_map = self._label_map(sv)
        display_map = self._display_as_map(sv)
        form_overrides = self._form_overrides(sv)
        detail_overrides = self._detail_overrides(sv)

        if primary:
            out["primaryFields"] = primary
        if label_map:
            out["typeNameLabelMap"] = label_map
        if display_map:
            out["typeNameUiSchemaOptionsMap"] = display_map
        if form_overrides:
            out["uischemaScopeOverrides"] = form_overrides
        if detail_overrides:
            out["detailUiSchemaScopeOverrides"] = detail_overrides

        return json.dumps(out, indent=2, ensure_ascii=False) + "\n"

    # ------------------------------------------------------------------ #
    # Per-section builders                                                 #
    # ------------------------------------------------------------------ #

    def _primary_fields(self, sv: SchemaView) -> dict:
        result: dict[str, dict] = {}
        for cls_name, cls in sv.all_classes().items():
            entry: dict[str, str] = {}
            for ann_key, field_key in (
                ("gra:primaryLabel", "label"),
                ("gra:primaryDescription", "description"),
                ("gra:primaryImage", "image"),
            ):
                val = _get_ann(cls, ann_key)
                if val is not None:
                    entry[field_key] = str(val)
            if entry:
                result[cls_name] = entry
        return result

    def _label_map(self, sv: SchemaView) -> dict:
        result: dict[str, str] = {}
        for cls_name, cls in sv.all_classes().items():
            val = _get_ann(cls, "gra:label")
            if val is not None:
                result[cls_name] = str(val)
        return result

    def _display_as_map(self, sv: SchemaView) -> dict:
        _DISPLAY_MAP = {
            "dropdown": {"dropdown": True},
            "chips": {"chips": True},
        }
        result: dict[str, dict] = {}
        for cls_name, cls in sv.all_classes().items():
            val = _get_ann(cls, "gra:displayAs")
            if val is not None:
                key = str(val).strip()
                if key in _DISPLAY_MAP:
                    result[cls_name] = _DISPLAY_MAP[key]
        return result

    def _form_overrides(self, sv: SchemaView) -> dict:
        result: dict[str, dict] = {}
        for cls_name, cls in sv.all_classes().items():
            scope_override: dict[str, dict] = {}
            skip_scope: list[str] = []
            for slot_name, slot_usage in cls.slot_usage.items():
                form_ann = _get_ann(slot_usage, "gra:form")
                if form_ann is None:
                    continue
                scope = f"#/properties/{slot_name}"
                ctrl: dict[str, Any] = {"type": "Control", "scope": scope}
                if isinstance(form_ann, dict):
                    if form_ann.get("label"):
                        ctrl["label"] = form_ann["label"]
                    if form_ann.get("options"):
                        ctrl["options"] = form_ann["options"]
                    if form_ann.get("skip"):
                        skip_scope.append(scope)
                scope_override[scope] = ctrl
            cls_entry: dict[str, Any] = {}
            if scope_override:
                cls_entry["scopeOverride"] = scope_override
            if skip_scope:
                cls_entry["skipScope"] = skip_scope
            if cls_entry:
                result[cls_name] = cls_entry
        return result

    def _detail_overrides(self, sv: SchemaView) -> dict:
        result: dict[str, dict] = {}
        for cls_name, cls in sv.all_classes().items():
            skip_scope: list[str] = []
            scope_override: dict[str, dict] = {}
            for slot_name, slot_usage in cls.slot_usage.items():
                detail_ann = _get_ann(slot_usage, "gra:detail")
                if detail_ann is None:
                    continue
                scope = f"#/properties/{slot_name}"
                if isinstance(detail_ann, dict):
                    if detail_ann.get("skip"):
                        skip_scope.append(scope)
                    if detail_ann.get("label"):
                        scope_override[scope] = {
                            "type": "Control",
                            "scope": scope,
                            "label": detail_ann["label"],
                        }
            cls_entry: dict[str, Any] = {}
            if skip_scope:
                cls_entry["skipScope"] = skip_scope
            if scope_override:
                cls_entry["scopeOverride"] = scope_override
            if cls_entry:
                result[cls_name] = cls_entry
        return result
