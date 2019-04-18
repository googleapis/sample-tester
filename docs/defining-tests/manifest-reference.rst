.. _defining-tests/manifest-reference:

Manifest file format
--------------------

A manifest file is a YAML file that associates each artifact (sample)
of interest on disk with a series of tags that can be used to uniquely
identify that artifact. Right now both versions "1" and "2" of the
manifest file format are supported; version "2" is a superset of
version "1".

The fundamental unit in a manifest is the "item", which is a
collection of tag name/value pairs; each unit should correspond to
exactly one artifact on disk. 

Since a lot of the artifacts will share part or all of some tags
(for example, the initial directory components, or the binary used to
execute them), "items" are grouped into "sets". Each set may define
its own tag name/value pairs. These pairs are applied to each of the
items inside the set as follows:

#. If the item does not define a given tag name, then the tag
   name/value pair in its set is applied to the item.
#. If the item does define a given tag name, then the corresponding
   tag value specified in the set is prepended to the corresponding
   value specified in the item. This is particularly useful in the
   case of paths: the set may define the common path for all of its
   items, and each item specifies its unique trailing directories and
   filename.

In manifest version "2", tag values can include references to other
tags: the value of tag “A” can reference the value of tag “B” by
enclosing the name of tag “B” in curly brackets: ``{TAG_B_NAME}``. For
example:

.. code-block:: yaml
		
   name: Zoe
   greeting: "Hello, {name}!
   
will define the same sets of tags as

.. code-block:: yaml

   name: Zoe
   greeting: "Hello, Zoe!"

While tags can be referenced arbitrarily deep, no reference can form a
loop (ie a tag directly or indirectly including itself).

Tags for sample-tester
----------------------

Some manifest tags are of special interest to the sample test runner:

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
     
* (deprecated) ``bin``: The executable used to run the sample. The
  sample ``path`` and arguments are appended to the value of this tag
  to form the command line that the tester runs.

**Advanced usage**: you can tell sample-tester to use different key names than the ones above. For example, to use keys ``some_name``, ``how_to_call``, and ``switch_path`` instead of ``sample``, ``invocation``, and ``chdir``, respectively, you would simply specify this flag when calling sample-tester:


  .. code-block:: bash

     -c tag:some_name:how_to_call,switch_path


Here's a typical manifest file:

.. literalinclude:: language.manifest.yaml
   :start-after: Example manifest file

