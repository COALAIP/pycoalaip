Library Reference
=================

.. automodule:: coalaip


``coalaip``
-----------

.. automodule:: coalaip.coalaip

.. autoclass:: CoalaIp
    :members:

    .. automethod:: __init__


``entities``
------------

.. automodule:: coalaip.entities

.. _core-entities:

``Core Entities``
^^^^^^^^^^^^^^^^^

.. note:: Most of these core entity classes have their functionality
          implemented through :class:`~.Entity`. See :class:`~.Entity`
          for an overview of the base functionality of each of these
          core entities.

.. autoclass:: Work
    :members:

.. autoclass:: Manifestation
    :members:

.. autoclass:: Right
    :members:

.. autoclass:: Copyright
    :members:

``Base Entities``
^^^^^^^^^^^^^^^^^

Base functionality for the models above. These should never be instantiated;
prefer one of the :ref:`core-entities` instead.

.. autoclass:: Entity
    :members:

.. autoclass:: TransferrableEntity
    :members:


``models``
----------

.. automodule:: coalaip.models

.. autoclass:: Model
    :members:

    .. automethod:: __init__

.. autoclass:: LazyLoadableModel
    :members:

    .. automethod:: __init__


``data formats``
----------------

.. automodule:: coalaip.data_formats

.. autoclass:: DataFormat


``exceptions``
--------------

.. automodule:: coalaip.exceptions

.. autoclass:: CoalaIpError

.. autoclass:: IncompatiblePluginError

.. autoclass:: ModelError

.. autoclass:: ModelDataError

.. autoclass:: ModelNotYetLoadedError

.. autoclass:: PersistenceError

.. autoclass:: EntityCreationError

.. autoclass:: EntityNotFoundError

.. autoclass:: EntityNotYetPersistedError

.. autoclass:: EntityPreviouslyCreatedError

.. autoclass:: EntityTransferError


``plugin``
----------

.. automodule:: coalaip.plugin

.. autoclass:: AbstractPlugin
    :members:
