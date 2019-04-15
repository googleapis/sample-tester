.. _defining-tests/manifest-reference:

Manifest file format
--------

A manifest file is a YAML file that associates each artifact (sample)
of interest on disk with a series of tags that can be used to uniquely
identify that artifact. Right now both versions "1" and "2" of the
manifest file format are supported; version "2" is a superset of version "1".

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

While tags can be referenced arbitrarily deep, no reference can form a loop (ie a tag directly or indirectly including itself).

Tags for sample-tester
----

Some manifest tags are of special interest to the sample test runner,
such as those named ``environment``, ``path``, ``bin``, and
``sample``. These four are interpreted, respectively, as the
programming language of the given artifact, the path to that artifact
on disk, the binary used to execute the artifact (if the artifact is
not itself executable), and the unique sample identifier by which to
quickly identify the artifact in any language. In particular,
artifacts with the same ``sample`` but different ``environment``\ s
are taken to represent the same conceptual sample, but implemented in
the different programming languages or execution environments; this
allows a test specification to refer to the ``sample``\ s only and the
runner will then run that test for each of the ``emvironment``\ s
available.

.. literalinclude:: language.manifest.yaml
   :start-after: Example manifest file

