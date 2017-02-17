=========
pycoalaip
=========

.. image:: https://img.shields.io/pypi/v/coalaip.svg
        :target: https://pypi.python.org/pypi/coalaip

.. image:: https://img.shields.io/travis/bigchaindb/pycoalaip.svg
        :target: https://travis-ci.org/bigchaindb/pycoalaip

.. image:: https://img.shields.io/codecov/c/github/bigchaindb/pycoalaip/master.svg
    :target: https://codecov.io/github/bigchaindb/pycoalaip?branch=master

.. image:: https://readthedocs.org/projects/pycoalaip/badge/?version=latest
        :target: https://pycoalaip.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/bigchaindb/pycoalaip/shield.svg
     :target: https://pyup.io/repos/github/bigchaindb/pycoalaip/
     :alt: Updates


Python reference implementation for `COALA IP <https://github.com/coalaip/specs>`_.

* Development Status: Alpha
* Free software: Apache Software License 2.0
* Documentation: https://pycoalaip.readthedocs.io


Features
--------

* ``CoalaIp.generate_user()``: Create a user representation suitable for use
  with ``coalaip``
* ``CoalaIp.register_manifestation()``: Registering a ``Manifestation`` (and
  along with it, an associated parent ``Work`` and a ``Copyright`` of the
  ``Manifestation``)
* ``CoalaIp.derive_right()``: Derivation of a ``Right`` from an allowing source
  ``Right`` or ``Copyright``
* ``CoalaIp.transfer_right()``: Transfer of a ``Right`` or ``Copyright`` from
  the current owner to a new owner
* Querying the ownership history of an COALA IP entity

To learn more about how to use these features, you may be interested in the
`usage section of the docs <https://pycoalaip.readthedocs.io/en/latest/usage.html>`_.


TODO
----

* Host COALA IP JSON-LD definitions and set ``<coalaip placeholder>`` to the
  purl for the definitions.
* Support IPLD serialization


Packaging
---------

Bumping versions:

.. code-block:: bash

    $ bumpversion patch

Releasing to pypi:

.. code-block:: bash

    $ make release
    $ twine upload dist/*


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
