# Sample Tester

Version 0.7.2


## Setup
1. Ensure you have credentials set up

   ```shell
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/creds.json
   ```
   
2. Install the necessary packages:
   ```shell
   pip install pyyaml
   ```

## Setting up the test
Set up the test plan as in `./examples/lang_region/language.test.yaml`. That sample test has three equivalent representations of the same test, one with absolute artifact paths in the imperative style, the second with canonical artifact paths in the imperative style, and the third with canonical artifact paths in the declarative style. (See NOTES below). Some features that may not be obvious from that test file:

1. You can have any number of test suites.
2. Each test suite can have `setup`, `teardown`, and `cases` sections.
3. The `cases` section is a list of test cases. For _each_ test case, `setup` is executed before running the test case and `teardown`is executed after.
4. `setup`, `teardown` and each `cases[...].spec` is a list of directives and arguments. The directives can be any of the following YAML directives:
   - `log`: print the arguments, printf style
   - `uuid`: return a uuid (if called from yaml, assign it to the variable names as an argument)
   - `shell`: run in the shell the command specified in the argument
   - `call`: call the artifact named in the argument, error if the call fails
   - `call_may_fail`: call the artifact named in the argument, do not error even if the call fails
   - `assert_contains`: require the given variable to contain a string
   - `assert_not_contains`: require the given variable to not contain a string
   - `assert_success`: require that the exit code of the last `call_may_fail` was 0. If the preceding call was a just a `call`, it would have already failed on a non-zero exit code.
   - `assert_failure`: require that the exit code of the last `call_may_fail` or `call` was NOT 0. Note, though, that if we're executing this after just a `call`, it must have succeeded so this assertion will fail.
   - `env`: assign the value of an environment variable to a testcase variable
   - `code`: execute the argument as a chunk of Python code. The other directives above are available as Python calls with the names above. In addition, the following functions are available inside Python `code` only: 
      - `fail`: mark the test as having failed, but continue executing
      - `abort`: mark the test as having failed and stop executing
      - `assert_that`: if the condition in the first argument is false, abort the test
5. In the usual case, you will be using the "manifest" convention. Thus, you will need one or more manifest files (`*.manifest.yaml`) listing the path and identifiers for each sample. See `convention/manifest/sample.manifest.yaml` for an explanation of the structure of the `*.manifest.yaml` files.

## Manifest File

A manifest file is a YAML file that associates each artifact (sample) of interest on disk with a series of tags that can be used to uniquely identify that artifact. Right now only version "1" of the manifest file format is supported, but we have the version as the first field in the file to support different schemas in the future.

The fundamental unit in a manifest is the "item", which is a collection of label name/value pairs; each unit should correspond to exactly one artifact on disk. Some labels are of special interest to the sample test runner, such as those named `language`, `path`, `bin`, and `region_tag`. These four are interpreted, respectively, as the programming language of the given artifact, the path to that artifact on disk, the binary used to execute the artifact (if the artifact is not itself executable), and the unique region tag by which to quickly identify the artifact for the given language. In particular, artifacts with the same `region_tag` but different `language`s are taken to represent the same conceptual sample, but implemented in the different programming languages; this allows a test specification to refer to the `region_tag`s only and the runner  will then run that test for each of the `language`s available.

Since a lot of the artifacts will share part or all of some labels (for example, the initial directory components, or the binary used to execute them), "items" are grouped into "sets". Each set may define its own label name/value pairs. These pairs are applied to each of the items inside the set as follows:

1. If the item does not define a given label name, then the label name/value pair in its set is applied to the item.
2. If the item does define a given label name, then the corresponding label value specified in the set is prepended to the corresponding value specified in the item. This is particularly useful in the case of paths: the set may define the common path for all of its items, and each item specifies its unique trailing directories and filename.

See `./sample.manifest.yaml` for a concrete, commented example.

## Running tests
The common usage is:

```shell
./sampletester TEST.yaml [TEST.yaml ...] [MANIFEST.manifest.yaml ...]
```

where:

* there can be any number of `TEST.yaml` test plan files
* there can be any number of `MANIFEST.manifest.yaml` manifest files

This will use the default "convention", which tries to resolve the sample references in the test plan files by looking at the manifest for entries matching the language being run and the refernce name as a "region tag".

For example, my own invocation to run a test on the fake samples under `testdata/` is

```shell
./sampletester -s examples/lang_region/language.test.yaml examples/lang_region/language.manifest.yaml 
```
   
Note that `sampletester` is silent by default and simply exits with a non-zero code if there was any error in the flags, test config, or test execution. If you're interested in seeing results on stdout, you'll probably want to run with the `-s` flag. If you want to debug a test failure, you'll want `-s -v`

The flag `--xunit=FILE` outputs a test summary in xUnit format to `FILE` (use `-` for stdout).

## Advanced usage

If  you want to change the convention in use, you can pass the `--convention=NAME` flag. You can provide any number of paths to the convention. (In the default case, the paths are just manifest files, but these could be anything).

```shell
./sampletester TEST.yaml [--convention=CONVENTION] [TEST.yaml ...] [USERPATH ...]
```
If you want to define your own convention, just add a package or module (whose name will become the convention name) under `convention/`. Have that package or module export a function `test_environments` which returns an array of instance of child classes of `testenv.Base`.
