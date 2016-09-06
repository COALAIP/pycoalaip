About this Documentation
========================

This section contains instructions to build and view the documentation locally.

If you do not have a clone of the repo, you need to get one.


Building the documentation
--------------------------
To build the docs, simply run

.. code-block:: bash

    $ make docs


Viewing the documentation
-------------------------
You can either start a little web server locally, or open the HTML files with
your browser.

To start a web server at http://localhost:5555/

.. code-block:: bash

    # In project root, after making the docs
    $ cd docs/_build/html/ && python -m SimpleHTTPServer 5555

Alternatively, open the `docs/_build/html/index.html` file in your web browser.


Making changes
--------------
Rebuild the docs and refresh the page on your web browser.
