Defining tests
--------------

1. You can have any number of test suites.
2. Each test suite can have ``setup``, ``teardown``, and ``cases`` sections.
3. The ``cases`` section is a list of test cases. For _each_ test case, ``setup`` is executed before running the test case and ``teardown`` is executed after.
4. ``setup``, ``teardown`` and each ``cases[...].spec`` is a list of directives and arguments. The directives can be any of the following YAML directives:
   
   - ``log``: print the arguments, printf style
   - ``uuid``: return a uuid (if called from yaml, assign it to the variable names as an argument)
   - ``shell``: run in the shell the command specified in the argument
   - ``call``: call the artifact named in the argument, error if the call fails
   - ``call_may_fail``: call the artifact named in the argument, do not error even if the call fails
   - ``assert_contains``: require the given variable to contain a string
   - ``assert_not_contains``: require the given variable to not contain a string
   - ``assert_success``: require that the exit code of the last ``call_may_fail`` was 0. If the preceding call was a just a ``call``, it would have already failed on a non-zero exit code.
   - ``assert_failure``: require that the exit code of the last ``call_may_fail`` or ``call`` was NOT 0. Note, though, that if we're executing this after just a ``call``, it must have succeeded so this assertion will fail.
   - ``env``: assign the value of an environment variable to a testcase variable
   - ``code``: execute the argument as a chunk of Python code. The other directives above are available as Python calls with the names above. In addition, the following functions are available inside Python ``code`` only 
      - ``fail``: mark the test as having failed, but continue executing
      - ``abort``: mark the test as having failed and stop executing
      - ``assert_that``: if the condition in the first argument is false, abort the test
5. In the usual case, you will be using the "manifest" convention. Thus, you will need one or more manifest files (``*.manifest.yaml``) listing the path and identifiers for each sample. See ``convention/manifest/sample.manifest.yaml`` for an explanation of the structure of the ``*.manifest.yaml`` files.
