.. _defining-tests:

Defining tests
--------------

To execute a test, you will need:

#. A “test plan”, defined via one or more ``*.yaml`` files. Here's an
   example:
   
   .. literalinclude:: language.test.yaml
      :start-after: The most typical use pattern is the following
      :end-before: Above is the typical usage
      :caption:
         
   See the :ref:`defining-tests/testplan-reference` page for
   information on the yaml directives available in the testplan, and
   how to use them directly via embedded Python code.

#. A “manifest”, defined via one or more ``*.manifest.yaml``
   files. Here's an example:

   .. literalinclude:: language.manifest.yaml
      :start-after: Example manifest file
      :caption:
         
   See the :ref:`defining-tests/manifest-reference` page for an
   explanation of the manifest.
   

.. toctree::
   :maxdepth: 2
   :caption: References:

   testplan-reference
   manifest-reference
