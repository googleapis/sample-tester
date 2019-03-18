.. _defining-tests/manifest-reference:

Manifest
--------

A manifest file is a YAML file that associates each artifact (sample)
of interest on disk with a series of tags that can be used to uniquely
identify that artifact. Right now only version "1" of the manifest
file format is supported, but we have the version as the first field
in the file to support different schemas in the future.

The fundamental unit in a manifest is the "item", which is a
collection of label name/value pairs; each unit should correspond to
exactly one artifact on disk. Some labels are of special interest to
the sample test runner, such as those named ``language``, ``path``,
``bin``, and ``region_tag``. These four are interpreted, respectively,
as the programming language of the given artifact, the path to that
artifact on disk, the binary used to execute the artifact (if the
artifact is not itself executable), and the unique region tag by which
to quickly identify the artifact for the given language. In
particular, artifacts with the same ``region_tag`` but different
``language``\ s are taken to represent the same conceptual sample, but
implemented in the different programming languages; this allows a test
specification to refer to the ``region_tag``\ s only and the runner
will then run that test for each of the ``language``\ s available.

Since a lot of the artifacts will share part or all of some labels
(for example, the initial directory components, or the binary used to
execute them), "items" are grouped into "sets". Each set may define
its own label name/value pairs. These pairs are applied to each of the
items inside the set as follows:

#. If the item does not define a given label name, then the label
   name/value pair in its set is applied to the item.
#. If the item does define a given label name, then the corresponding
   label value specified in the set is prepended to the corresponding
   value specified in the item. This is particularly useful in the
   case of paths: the set may define the common path for all of its
   items, and each item specifies its unique trailing directories and
   filename.

.. literalinclude:: language.manifest.yaml
   :start-after: Example manifest file

