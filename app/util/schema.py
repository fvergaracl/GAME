from typing import Optional

from pydantic._internal._model_construction import ModelMetaclass


class AllOptional(ModelMetaclass):
    """
    Metaclass that makes all fields of a Pydantic model optional and
    defaulting to ``None``. In Pydantic v2, ``Optional[X]`` no longer implies
    a ``None`` default, so the metaclass also injects defaults to preserve v1
    behavior expected by callers.
    """

    def __new__(mcs, name, bases, namespaces, **kwargs):
        annotations = dict(namespaces.get("__annotations__", {}))
        for base in bases:
            annotations.update(getattr(base, "__annotations__", {}))
        for field, typ in list(annotations.items()):
            if field.startswith("__"):
                continue
            annotations[field] = Optional[typ]
            namespaces.setdefault(field, None)
        namespaces["__annotations__"] = annotations
        return super().__new__(mcs, name, bases, namespaces, **kwargs)
