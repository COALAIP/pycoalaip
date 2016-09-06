=======
Plugins
=======

``pycoalaip`` requires a persistence layer plugin to be used in order to
persist COALA IP entities to a distributed ledger, database, or file storage
system.


Available Plugins
-----------------

- `BigchainDB <https://github.com/bigchaindb/pycoalaip-bigchaindb>`_


Writing a Plugin
----------------

Writing a plugin for ``pycoalaip`` is relatively simple. We use the
`pycoalaip-{plugin_name}` naming scheme for plugin packages.

A plugin is expected to subclass from :class:`~coalaip.plugin.AbstractPlugin`
and implement all the abstract methods and properties, following the API laid
out in the :class:`~coalaip.plugin.AbstractPlugin`'s documentation.

To make your plugin discoverable by name to ``pycoalaip``, you should also set
an entry point in your ``setup.py`` for the ``coalaip_plugin`` namespace.
Taking the BigchainDB plugin as an example, this may look something like::

    setup(
        ...
        entry_points={
            'coalaip_plugin': 'bigchaindb = coalaip_bigchaindb.plugin:Plugin'
        },
        ...
    )
