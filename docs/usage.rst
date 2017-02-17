=====
Usage
=====

To use pycoalaip in a project:

.. code-block:: python

    import coalaip

----------
Quickstart
----------

To get started with ``coalaip``, you should first pick a persistence layer (and
an accompanying plugin) to use. For a list of available persistence layer
plugins, see :ref:`here <available-plugins>`.

Once you've configured your chosen plugin, the main workflow to follow is:

1. Create an instance of ``CoalaIp``;
1. Generate users for yourself and other parties;
1. Register a ``Manifestation`` entity (and its accompanying ``Work`` and
``Copyright`` entities) for your IP;
1. Derive a specific ``Right`` from your IP's ``Copyright`` (or another
``Right`` that pertains to your IP); and
1. If desired, transfer the specific ``Right`` to another party, to record a
legal transaction relating to the ``Right`` (e.g. a transfer of ownership,
a loan, etc).

.. note::

    Each of ``CoalaIp.register_manifestation()``, ``CoalaIp.derive_right()``,
    and ``CoalaIp.transfer_right()`` have optional arguments to cover alternate
    use cases that are not explained here.

    You may be interested in looking at the :doc:`library reference <libref>`
    for their complete documentation.

.. warning::

    In the current implementation, operations that use the persistence layer
    are **NOT** ensured to succeed, and you may find that some operations need
    to be repeated.

    A good example of this is if a storage requiring non-neglible consensus
    (e.g. BigchainDB) is used: the implementation assumes that everything has
    succeeded if it was able to write to the storage rather than confirming
    (later) that what it wrote was actually accepted.

Creating an instance of ``CoalaIp``
===================================

Let's assume you have an instance of a persistence layer plugin ready.

.. code-block:: python

    from coalaip import CoalaIp

    plugin = Plugin(...)
    coalaip = CoalaIp(plugin)

Generating users
================

Representations of users are defined by the persistence layer plugin. You can
generate a user compatible with your chosen persistence layer by:

.. code-block:: python

    # Note that the plugin may dictate that you need to provide extra arguments
    # to this function
    user = coalaip.generate_user()

Registering a ``Manifestation``
===============================

Upon initial registration of a ``Manifestation``, a ``Work`` (if not provided)
and ``Copyright`` are automatically generated.

.. code-block:: python

    manifestation_data = {...}
    registration_result = coalaip.register_manifestation(manifestation_data,
                                                         copyright_holder=user)
    manifestation = registration_result['manifestation']
    work = registration_result['work']
    copyright = registration_result['copyright']

Deriving a specific ``Right``
=============================

You can create more specific ``Rights`` from source ``Rights`` or
``Copyrights`` if you are the current holder of the source ``Right``.

.. code-block:: python

    copyright = ...
    right_data = {...}
    right = coalaip.derive_right(right_data, current_holder=user,
                                 source_right=copyright)

Transferring a ``Right``
========================

Transfers of a ``Right`` will change ownership of the entity from the current
holder to a new holder. A ``RightsAssignment`` entity can also be encoded in a
transfer, holding more specific information about the particular details
related to the transaction, such as a agreed-upon contract between the two
parties, the time of the transaction, and etc.

.. code-block:: python

    right = ...
    current_holder = ... # user representation
    new_holder = ... # user representation
    rights_assignment_data = {...}
    rights_assignment = coalaip.transfer_right(right, rights_assignment_data,
                                               current_holder=current_holder,
                                               to=new_holder)

Querying for an ``Entity``'s ownership history
==============================================

Each entity returned has a ``.history()`` method and ``.current_owner``
property defined, in case you're interested in finding out the ownership
history of the entity.

Obtaining an instance of an ``Entity``
======================================

If you know you have COALA IP entities persisted, but don't have them in an
``Entity`` class (e.g. you saved the entities' IDs in a database, and now want
to use them), you can load an instance of an ``Entity`` by using the static
``.from_persist_id()`` method of that entity type.

.. code-block:: python

    from coalaip.entities import Manifestation

    manifestation_id = '...'
    manifestation = Manifestation.from_persist_id(manifestation_id,
                                                  plugin=plugin)

Doing so will generate a lazy-loaded entity for you to use. Accessing the
entity's data for the first time will load the entity from the persistence
layer (which may error); if you'd like to load it immediately, you can either
call ``.load()`` or use the ``force_load`` flag in ``.from_persist_id()``:

.. code-block:: python

    manifestation = Manifestation.from_persist_id(manifestation_id,
                                                  plugin=plugin)
    manifestation.load()

    # Or
    manifestation = Manifestation.from_persist_id(manifestation_id,
                                                  force_load=True,
                                                  plugin=plugin)


---------
Reference
---------

See the :doc:`library reference <libref>` for a complete reference of all
available classes and functions.
