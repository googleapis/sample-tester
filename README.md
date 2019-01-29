# Sample Tester

Version 0.5


**_Disclaimers_**: Invocation and test format **will change**. The code started off as a prototype, and has not been optimized for performance, elegance, or clarity yet (though it shouldn't be horrible).

Refer to spec at [go/actools-sample-tester](go/actools-sample-tester).

## Setup
1. Ensure you have credentials set up

```shell
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/creds.json
```
   
2. Install the necessary packages in your PIP environment
   The virtual environment set up for running artman should be sufficient (thought not all the those packages may be necessary)
   TODO: trim down the list of packages

## Setting up the test
Set up the test plan as in `./example/example.language.yaml`. That sample test has two equivalent representations of the same test, one with absolute artifact paths and the other with canonical artifact paths. (See NOTES below). Some features that may not be obvious from that test file:

1. You can have any number of test suites.
2. Each test suite can have `setup`, `teardown`, and `cases` sections.
3. The `cases` section is a list of test cases. For _each_ test case, `setup` is executed before running the test case and `teardown`is executed after.
4. `setup`, `teardown` and each `cases[...].spec` is a list of directives and arguments. The directives can be any of the following YAML directives:
  - `call`: call the artifact named in the argument, error if the call fails
  - `call_may_fail`: call the artifact named in the argument, do not error even if the call fails
  - `shell`: run in the shell the command specified in the argument
  - `uuid`: return a uuid (if called from yaml, assign it to the variable names as an argument)
  - `print`: print the arguments, printf style
  - `fail`: mark the test as having failed, but continue executing
  - `abort`: mark the test as having failed and stop executing
  - `expect`: if the condition in the first argument is false, fail the test
  - `require`: if the condition in the first argument is false, abort the test
  - `expect_contains`: expect the given variable to contain a string
  - `require_contains`: require the given variable to contain a string
  - `expect_not_contains`: expect the given variable to not contain a string
  - `require_not_contains`: require the given variable to not contain a string
  - `code`: execute the argument as a chunk of Python code. The other directives above are available as Python calls.


## Running the test
The usage is:

    ```
    ./test_sample.py TEST.yaml [CONVENTION.py] [TEST.yaml ...] [USERPATH ...]`
    ```

    where `CONVENTION.py` is one of `convention/manifest/id_by_region.py` (default) or
    `convention/cloud/cloud.py`

    `USERPATH` depends on `CONVENTION`. For `id_by_region`, it should be a path to a
    `MANIFEST.manifest.yaml` file.
   
   
    For example, my own invocation to run a test on the fake samples under `testdata/` is
   
     ```
     ./test_sample.py convention/manifest/ex.language.test.yaml convention/manifest/ex.language.manifest.yaml
     ```
   

    
## NOTES

**tl;dr: some things will change soon**

* I am also in the process of implementing the feedback on [go/actools-sample-tester](go/actools-sample-tester). This will reduce the number of available directives, and rename some of them.
