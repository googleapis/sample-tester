# Sample Tester

Version: 0.7.8

**PRE-RELEASE**: This surface is not guaranteed to be stable. Breaking changes may still be applied.

## Installation
Refer to [the installation guide](./docs/installation.rst).

## Setup

To run against Google APIs, ensure you have credentials set up:

   ```shell
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/creds.json
   ```
   

## Setting up the test
Set up the test plan as in `./examples/lang_region/language.test.yaml`.

That test plan has three equivalent representations of the same test, one with absolute artifact paths in the imperative style, the second with canonical artifact paths in the imperative style, and the third with canonical artifact paths in the declarative style. (See NOTES below). The documentation on [defining tests](./docs/defining-tests.rst) highlights the key capabilities of test plan files.

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
               [--envs=REGEX] [--suites=REGEX] [--cases=REGEX]
               [--fail-fast]
               [--convention CONVENTION:ARG,ARGS]
```

where:

* there can be any number of `TEST.yaml` test plan files
* there can be any number of `MANIFEST.manifest.yaml` manifest files
* `--envs`, `--suites`, and `--cases` are Python-style regular expressions (beware shell-escapes!) to select which environments, suites, and cases to run, based on their names. All the environemnts, suites, or cases will be selected to run by default if the corresponding flag is not set. Note that if an environment is not selected, its suites are not selected regardless of `--suites`; if a suite is not selected, its testcases are not selected regardless of `--cases`.
* `--fail-fast` makes execution stop as soon as a failing test case is encountered, without executing any remaining test cases.
* `--convention` (or `-c`) can be used to specify both a particular convention to resolve the sample IDs to disk artifacts, and a list of comma-separated arguments to that convention. The default convention is `tag:region_tag`, which uses the `region_tag` key in the manifest files. To use, say, the `target` key in the manifest, simply pass `-c tag:target`.

For example, my own invocation to run a test on the fake samples under `testdata/` is

```shell
./sample-tester examples/convention-tag/language.test.yaml examples/convention-tag/language.manifest.yaml 
```

### Output

In all cases, `sample-tester` exits with a non-zero code if there were any errors in the flags, test config, or test execution. 

In addition, by default `sampletester` prints the status of test cases to stdout. This output is controlled by the following flags:

* `--verbosity` (`-v`): controls how much output to show for passing tests. The default is a "summary" view, but "quiet" (no output) and "detailed" (full case output) options are available.
* `--suppress_failures` (`-f`): Overrides the default behavior of showing output for failing test cases, regardless of the `--verbosity ` setting

The flag `--xunit=FILE` outputs a test summary in xUnit format to `FILE` (use `-` for stdout).

## Advanced usage

If  you want to change the convention in use, you can pass the `--convention=NAME` flag. You can provide any number of paths to the convention. (In the default case, the paths are just manifest files, but these could be anything).

```shell
./sampletester TEST.yaml [--convention=CONVENTION] [TEST.yaml ...] [USERPATH ...]
```
If you want to define your own convention, just add a package or module (whose name will become the convention name) under `convention/`. Have that package or module export a function `test_environments` which returns an array of instance of child classes of `testenv.Base`.

## Development

During development, run the `devcheck` script to run all tests and examples and verify they work as expected.

## Disclaimer

This is not an official Google product.


