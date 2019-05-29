.. _defining-tests/testplan-reference:

Testplan
--------

One of the inputs to sample-tester is the “testplan”, which outlines
how to run the samples and what checks to perform.

#. The testplan can be spread over any number of ``TESTPLAN.yaml``
   files.
#. You can have any number of test suites.
#. Each test suite can have ``setup``, ``teardown``, and ``cases``
   sections.
#. The ``cases`` section is a list of test cases. For _each_ test
   case, ``setup`` is executed before running the test case and
   ``teardown`` is executed after.
#. ``setup``, ``teardown`` and each ``cases[...].spec`` is a list of
   directives and arguments. The directives can be any of the
   following YAML directives:
   
   - ``log``: print the arguments, printf style
   - ``uuid``: return a uuid (if called from yaml, assign it to the
     variable names as an argument)
   - ``shell``: run in the shell the command specified in the argument
   - ``call``: call the artifact named in the argument; error if the
     call fails
   - ``call_may_fail``: call the artifact named in the argument; do
     not error even if the call fails
   - ``assert_contains``: require the given variable to contain a
     string (case-insensitively); abort the test case otherwise
   - ``assert_not_contains``: require the given variable to not
     contain a string (case-insensitively); abort the test case otherwise
   - ``assert_success``: require that the exit code of the last
     ``call_may_fail`` was 0; abort the test case otherwise. If the
     preceding call was a just a ``call``, it would have already
     failed on a non-zero exit code.
   - ``assert_failure``: require that the exit code of the last
     ``call_may_fail`` or ``call`` was NOT 0; abort the test case
     otherwise. Note, though, that if we're executing this after just
     a ``call``, it must have succeeded so this assertion will fail.
   - ``env``: assign the value of an environment (identified by
     ``variable``) variable to a test case variable (given by
     ``name``)
   - ``extract_match``: extrack regex matches into local variables
   - ``code``: execute the argument as a chunk of Python code. The
     other directives above are available as Python calls with the
     names above. In addition, the following functions are available
     inside Python ``code`` only:
     
      - ``fail``: mark the test as having failed, but continue executing
      - ``abort``: mark the test as having failed and stop executing
      - ``assert_that``: if the condition in the first argument is
        false, abort the test case

Here is an informative instance of a sample testfile:

.. literalinclude:: language.test.yaml
   :start-after: The most typical use pattern is the following

This test plan has three equivalent representations of the same test,
one with canonical artifact paths in the declarative style (using YAML
directives), the second with canonical artifact paths in the
imperative style (using a ``code`` block), and the third using
absolute artifact paths in the imperative style (which you would
rarely use, since th point of this tool is to not have to hardcode
different paths to semantically identical samples).

Unless you specify explicit paths to each sample (which means your
test plan cannot run for different languages/environments
simultaneously), you will need one or more manifest files
(``*.manifest.yaml``) listing the path and identifiers for each sample
in each language/environment. . Refer to the
:ref:`defining-tests/manifest-reference` page for an explanation of
the structure of the ``*.manifest.yaml`` files.

