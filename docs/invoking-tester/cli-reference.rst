.. _cli-reference:

Command-line flags
------------------

Basic usage
^^^^^^^^^^^

   .. code-block:: bash
                   
      sampletester TEST.yaml [TEST.yaml ...] [MANIFEST.manifest.yaml ...]
                   [--envs=REGEX] [--suites=REGEX] [--cases=REGEX]
                   [--fail-fast]


where:

* there can be any number of ``TEST.yaml`` :ref:`testplan <defining-tests/testplan-reference>` files
* there can be any number of ``MANIFEST.manifest.yaml`` :ref:`manifest <defining-tests/manifest-reference>` files
* ``--envs``, ``--suites``, and ``--cases`` are Python-style regular
  expressions (beware shell-escapes!) to select which environments,
  suites, and cases to run, based on their names. All the
  environemnts, suites, or cases will be selected to run by default if
  the corresponding flag is not set. Note that if an environment is
  not selected, its suites are not selected regardless of
  ``--suites``; if a suite is not selected, its testcases are not
  selected regardless of ``--cases``.
* ``--fail-fast`` makes execution stop as soon as a failing test case
  is encountered, without executing any remaining test cases.

Controlling the output
""""""""""""""""""""""

In all cases, ``sample-tester`` exits with a non-zero code if there were any errors in the flags, test config, or test execution. 

In addition, by default ``sampletester`` prints the status of test cases to stdout. This output is controlled by the following flags:

* ``--verbosity`` (``-v``): controls how much output to show for passing tests. The default is a "summary" view, but "quiet" (no output) and "detailed" (full case output) options are available.
* ``--suppress_failures`` (``-f``): Overrides the default behavior of showing output for failing test cases, regardless of the ``--verbosity`` setting
* ``--xunit=FILE`` outputs a test summary in xUnit format to ``FILE`` (use ``-`` for stdout).



Advanced usage
^^^^^^^^^^^^^^

The tester uses a "convention" to match sample names in the testplan
to actual, specific files on disk for given languages and
environments. Each convention may choose to take some set-up
arguments. You can specify an alternate convention and/or convention
arguments via the flag ``--convention=CONVENTION:ARG,ARGS``. The
default convention is ``tag:sample``, which uses the
``sample`` key in the manifest files. To use, say, the ``target``
key in the manifest, simply pass ``--convention=tag:target``.

If you want to define an additional convention, refer to the
documention in the repo on how to do so. If you do have such an
additional convention defined, you may use the ``--convention`` flag
to select it and give it any desired arguments, as above.
