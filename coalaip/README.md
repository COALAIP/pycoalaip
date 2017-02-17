`coalaip`
=========

The main components of `coalaip`:

- `coalaip.py`: User-facing functionality for registering Manifestations, deriving Rights, and
  transferring Rights. Hides away a lot of complexity and just expects the user to only have to deal
  with JSON data or already-created `Entity`s (from previous usage of the functions). **Requires a
  [persistence layer plugin](#plugins) to be used.**
- `entities.py`: Entity classes for each COALA IP entity.
    - Each `Entity` class holds a `Model` (that may be lazy-loadable, depending on the use case).
      `Entity`s are concerned with user-facing operations, such as serializing their data into
      different formats or loading data from a persistence layer. Instances of these classes are
      returned to the user by functions in `coalaip.py`.
- `models.py`: Generic models for holding data related to COALA IP entities.
- `plugin.py`: Abstract definition of the expected interface for persistence layer plugins to be
  used with this package.

Whenever possible, most instances of classes are immutable.


Plugins
-------

`coalaip` is dependent on a persistence layer plugin that implements the interface defined in
`plugin.py`. These plugins should handle any necessary connections and implementation details
related to the backing decentralized ledger, database, or file system.
