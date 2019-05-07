# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import os
import sys
import re
import yaml

from collections import OrderedDict
from glob import glob
from yaml import Dumper
from yaml.representer import SafeRepresenter

ALL_LANGS = ["python", "java", "csharp", "nodejs", "ruby", "php", "go"]

def gen_manifest():
	args = parse_args()
	ma = manifest(args.bin, args.chdir, args.env, args.samples)
	dump(ma, args.output)
	print("*********")
	print("Done.")
	print("*********")

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--env', help='Language to generate manifest for.')
	parser.add_argument('--output', required=True, help='The name of the output file, should include the manifest.yaml` extension.')
	parser.add_argument('--bin', help='Fills in the `bin` directive.')
	parser.add_argument('--chdir', help='Fills in the `chdir` directive.')
	parser.add_argument('samples', nargs='*', help='Relative paths of sample files.')
	args = parser.parse_args(sys.argv[2:])
	if args.env not in ALL_LANGS:
		print("invalid value: --env, should be one of [python, java, csharp, nodejs, ruby, php, go]")
		sys.exit("Unrecognized language.")
	return args

def base_manifest():
	manifest = OrderedDict()
	manifest['version'] = 2
	manifest['sets'] = []
	return manifest

def manifest(bin, chdir, env, samples):
	manifest = base_manifest()
	environment = OrderedDict()
	environment['environment'] = env
	if bin is not None:
		environment['bin'] = bin 
	if chdir is not None:
		environment['chdir'] = chdir
	# Force a trailing '/' to make it work with tester
	# However we should actually do `os.path.join` in sample-tester as well
	environment['path'] = os.getcwd() + "/"
	environment['__items__'] = path_sample_pairs(samples)
	manifest['sets'].append(environment)
	return manifest


def path_sample_pairs(samples):
	items = []

	for s in samples:
		for sample in glob(s):
			items.append({
				'path': sample,
				'sample': get_region_tag(os.path.join(os.getcwd(), sample))
			})
	return items


def get_region_tag(sample_file_path):
	start_region_tag_exp = r'\[START ([a-zA-Z0-9_]*)\]'
	end_region_tag_exp = r'\[END ([a-zA-Z0-9_]*)\]'
	region_tags = []
	with open(sample_file_path) as sample:
		sample_text = sample.read()
		start_region_tags = re.findall(start_region_tag_exp, sample_text)
		end_region_tags = re.findall(end_region_tag_exp, sample_text)
		
		for srt in start_region_tags:
			
			# We don't need those with '_cores'
			if 'core' in srt:
				continue

			if srt in end_region_tags:
				region_tags.append(srt)
	
	if not region_tags:
		sys.exit("Found no region tags.")

	if len(region_tags) > 1:
		sys.exit("Found too many region tags.")

	return region_tags[0]

def dict_representer(dumper, data):
  return dumper.represent_dict(data.items())

def dump(manifest, output):
	Dumper.add_representer(OrderedDict, dict_representer)
	Dumper.add_representer(str,
                       SafeRepresenter.represent_str)

	with open(output, 'w') as output_file:
			yaml.dump(manifest, output_file, Dumper=Dumper, default_flow_style=False)


if __name__ == '__main__':
	gen_manifest()
