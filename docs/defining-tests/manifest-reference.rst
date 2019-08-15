.. _defining-tests/manifest-reference:

Manifest file format
--------------------

A manifest contains one or more YAML documents that associate each
artifact (sample) of interest on disk with a series of metadata
tags. Multiple manifests can be specified by having multiple YAML
documents within a single configuration YAML file and/or having
multiple configuration YAML files. The YAML documents within each YAML
file are separated by the usual YAML start-document indicator,
``---``.

A manifest YAML document has the general structure:

.. code-block:: yaml
		
   ---
   type: manifest/XXX
   schema_version: 3
   XXX:
   - item1foo: value
     item1bar: value

#. The "manifest" in the ``type`` field defines this YAML document
   as a manifest. Other document types are silently ignored (this
   permits putting disparate YAML documents in the same file if
   desired).

   - For backwards compatibility, any document that does not have a 
     ``type:`` top-level field will be treated as a manifest if the file
     in which it was specified ends in ``.manifest.yaml``
     
#. The arbitrary value "XXX" in the ``type`` field defines the
   top-level YAML field ``XXX`` as containing the actual manifest.
#. The ``schema_version`` field is required.
#. Each item in the ``XXX`` list is simply a dictionary of tag keys
   and values. The tag keys that define the metadata used by
   sample-tester are described below.
#. Other top-level tags (outside of the ``XXX`` list) are
   ignored. They can thus be used for additional metadata not used by
   sample-tester, and/or for defining YAML anchors in order to reduce
   duplication in the manifest document.
   
Tag values can include references to other tags: the value of tag “A”
can reference the value of tag “B” by enclosing the name of tag “B” in
curly brackets: ``{TAG_B_NAME}``. For example:

.. code-block:: yaml
		
   name: Zoe
   greeting: "Hello, {name}!
   
will define the same sets of tags as

.. code-block:: yaml

   name: Zoe
   greeting: "Hello, Zoe!"

While tags can be referenced arbitrarily deep, no reference can form a
loop (ie a tag directly or indirectly including itself).

Here's a generic manifest file illustrating these features:

.. literalinclude:: sample.manifest.yaml
   :start-after: Generic manifest file


Tags for sample-tester
----------------------

You may define an arbitrary set of tags for any and all elements in
your manifest, the only restriction being that no tag name you specify
may begin with ``@`` (because that is how we identify "implicit tags";
see below). Moreover, some manifest tags are of special interest to
sample-tester:

* ``sample``: The unique ID for the sample.
* ``path``: The path to the sample source code on disk.
* ``environment``: A label used to group samples that share the same
  programming language or execution environment. In particular,
  artifacts with the same ``sample`` but different ``environment``\ s
  are taken to represent the same conceptual sample, but implemented
  in the different languages/environments; this allows a test
  specification to refer to the ``sample``\ s only and sample-tester
  will then run that test for each of the ``environment``\ s
  available.
* ``invocation``: The command line to use to run the sample. The
  invocation typically makes use of two features for flexibility:
  
  * manifest tag inclusion: By including a ``{TAG_NAME}``,
    ``invocation`` (just like any tag) can include the value of
    another tag.
  * tester argument substitution: By including a ``@args`` literal,
    the ``invocation`` tag can specify where to insert the sample
    parameters as determined by the sample-tester from the test plan
    file.

  Thus, the following would be the typical usage for Java, where each
  sample item in the manifest includes a ``class_name`` tag and a
  ``jar`` tag:

  .. code-block:: yaml

     invocation: "java {jar} -D{class_name} -Dexec.arguments='@args'"

* ``chdir``: The working directory to be in before invoking the
  sample.
* (deprecated) ``bin``: The executable used to run the sample. The
  sample ``path`` and arguments are appended to the value of this tag
  to form the command line that the tester runs.

The sample-test runner also automatically adds certain **implicit
tags** to manifest elements when it reads them from YAML
files. Implicit tag names all begin with the symbol ``@``:

* ``@manifest_source``: The full path, including filename, to the
  manifest file from which this particular element was read.
* ``@manifest_dir``: The directory part of ``@manifest_source``,
  without the trailing filename. For example, depending on your
  particular set-up, you may wish to reference ``{@manifest_dir}`` as
  part of the value of your ``chdir`` tag.
  

**Advanced usage**: you can tell sample-tester to use different key names than the ones above. For example, to use keys ``some_name``,  ``how_to_call``, and ``switch_path`` instead of ``sample``,  ``invocation``, and ``chdir``, respectively, you would simply specify  this flag when calling sample-tester:


  .. code-block:: bash

     -c tag:some_name:how_to_call,switch_path


Here's a typical manifest file:

.. literalinclude:: language.manifest.yaml
   :start-after: Example manifest file

