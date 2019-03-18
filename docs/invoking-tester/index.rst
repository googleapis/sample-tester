Running tests
-------------

To run the tests you have :ref:`defined <defining-tests>`, do the following:

#. Prepare your environment. For example, to run tests against Google
   APIs, ensure you have credentials set up:

   .. code-block:: bash
                   
      export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/creds.json
   

#. Run the tester, specifying your manifest (any number of
   ``*.manifest.yaml`` files) and test plan (any number of other
   ``*.yaml`` files):

   .. code-block:: bash
                   
      sample-tester examples/convention-tag/language.test.yaml examples/convention-tag/language.manifest.yaml

   
.. toctree::
   :maxdepth: 2
   :caption: References:

   cli-reference
