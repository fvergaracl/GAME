from typing import Optional

from pydantic._internal._model_construction import ModelMetaclass


def _namespace_annotations(namespaces: dict) -> dict:
    """
    Return the class-body annotations from a class namespace, portably across
    Python versions.

    On Python <= 3.13 the annotations are stored eagerly under
    ``__annotations__``. On Python >= 3.14 (PEP 649/749) annotation evaluation
    is deferred: the class body exposes an ``__annotate_func__`` callable and
    ``__annotations__`` is absent from the namespace, so reading that key
    directly silently drops every field and Pydantic then rejects the leftover
    ``Field(...)`` values with "requires a type annotation".
    """
    annotations = namespaces.get("__annotations__")
    if annotations is not None:
        return dict(annotations)
    annotate = namespaces.get("__annotate_func__")
    if annotate is not None:
        import annotationlib  # Python 3.14+ stdlib; only reached there.

        return dict(annotate(annotationlib.Format.VALUE))
    return {}


class AllOptional(ModelMetaclass):
    """
    Metaclass that makes all fields of a Pydantic model optional and
    defaulting to ``None``. In Pydantic v2, ``Optional[X]`` no longer implies
    a ``None`` default, so the metaclass also injects defaults to preserve v1
    behavior expected by callers.
    """

    def __new__(mcs, name, bases, namespaces, **kwargs):
        annotations = _namespace_annotations(namespaces)
        for base in bases:
            annotations.update(getattr(base, "__annotations__", {}))
        for field, typ in list(annotations.items()):
            if field.startswith("__"):
                continue
            annotations[field] = Optional[typ]
            namespaces.setdefault(field, None)
        namespaces["__annotations__"] = annotations
        return super().__new__(mcs, name, bases, namespaces, **kwargs)
