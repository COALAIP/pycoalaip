Library Reference
=================

.. automodule:: coalaip


``coalaip``
-----------

.. automodule:: coalaip.coalaip

.. autoclass:: CoalaIp
    :members:

    .. automethod:: __init__


``models``
----------

.. automodule:: coalaip.models

.. _core-models:

``Core Models``
^^^^^^^^^^^^^^^

Usually, these classes shouldn't be directly instantiated; instead, you should
rely on the high-level functions available in :class:`~coalaip.coalaip.CoalaIp`
that produce instances of these models as part of their output.

.. autoclass:: Work
    :members:

    .. automethod:: __init__

.. autoclass:: Manifestation
    :members:

    .. automethod:: __init__

.. autoclass:: Copyright
    :members:

    .. automethod:: __init__

``Base Models``
^^^^^^^^^^^^^^^

Base functionality for the models above. These should never be instantiated;
prefer one of the :ref:`core-models` instead.

.. autoclass:: CoalaIpEntity
    :members:

    .. automethod:: __init__

.. autoclass:: CoalaIpTransferrableEntity
    :members:

    .. automethod:: __init__

.. autoclass:: Creation
    :members:

    .. automethod:: __init__

.. autoclass:: Right
    :members:

    .. automethod:: __init__


``exceptions``
--------------

.. automodule:: coalaip.exceptions

.. autoclass:: EntityError

.. autoclass:: EntityCreationError

.. autoclass:: EntityNotFoundError

.. autoclass:: EntityNotYetPersistedError

.. autoclass:: EntityPreviouslyCreatedError

.. autoclass:: ModelError

.. autoclass:: ModelDataError

.. autoclass:: ModelNotYetLoadedError


``plugin``
----------

.. automodule:: coalaip.plugin

.. autoclass:: AbstractPlugin
    :members:
