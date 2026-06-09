==================
Codebase Reference
==================

.. admonition:: Who is this page for?
   :class: note

   Contributors. This is the **auto-generated** API reference, pulled straight
   from the source docstrings by Sphinx ``autodoc``. It is the ground truth
   for signatures and types; the prose pages (:doc:`architecture`,
   :doc:`dsl-engine`) explain *why*.

How to read it
==============

The tree below mirrors the package layout described in :doc:`architecture`.
The fastest entry points by intent:

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - You want…
     - Start at
   * - The HTTP surface
     - ``app.api.v1.endpoints`` - one module per resource group.
   * - Business logic
     - ``app.services`` - the orchestration layer.
   * - Persistence
     - ``app.repository`` - async CRUD over SQLAlchemy.
   * - The schema
     - ``app.model`` (tables) and ``app.schema`` (wire contracts).
   * - The scoring engine
     - ``app.engine`` - built-ins, registry, and the DSL pipeline.
   * - Wiring & config
     - ``app.core`` (config, container, database) and ``app.middlewares``.

.. tip::

   Docstrings here follow the **Google style** (parsed by ``napoleon``).
   ``[source]`` links next to each entry jump to the code. When you add or
   change a public function, update its docstring - this page regenerates from
   it on every deploy.

Full module index
=================

.. toctree::
   :maxdepth: 2

   api/app

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
