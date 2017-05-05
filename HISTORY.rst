=======
History
=======

0.0.2 (2017-05-05)
------------------

Some changes during the OMI hackfest!

Some highlights:

* Add `register_work` method to enable registering a work without
  necessarily registering a manifestation.


0.0.1 (2017-02-17)
------------------

First alpha release on PyPI.

Additional features added with no backwards-incompatible interface changes.
COALA IP models are backwards-incompatible to previous versions due to upgrades
related to spec changes.

Some highlights:

* Queryability of an Entity's ownership history and current owner
* Entities can be given a custom ``@id``
* Additional sanity checks employed when deriving Rights, to ensure that a
  correct source Right and current holder are given
* Update COALA IP models to latest spec
* Added usage documentation


0.0.1.dev3 (2016-12-06)
-----------------------

Lots of changes and revisions from 0.0.1.dev2. Totally incompatible from
before.

Some highlights:

* Implemented Rights derivation (from existing Rights and Copyrights)
* Implemented Rights transfers
* Entities are now best-effort immutable
* Support for loading Entities from a connected persistence layer

0.0.1.dev2 (2016-08-31)
-----------------------

* Fix packaging on PyPI

0.0.1.dev1 (2016-08-31)
-----------------------

* Development (pre-alpha) release on PyPI.
