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
from yaml import CDumper as Dumper
from yaml.representer import SafeRepresenter

# Only python is supported for now
SUPPORTED_LANGS = ["python"]
ALL_LANGS = ["python", "java", "csharp", "nodejs", "ruby", "php", "go"]

def gen_manifest():
	args = parse_args()
	if args.lang == 'python':
		manifest = python_manifest(args.sample_dir)
		dump(manifest, args.output_dir, args.output_name)
	else:
		sys.exit("Unrecognized languages.")
	print("*********")
	print("Done.")
	print("*********")

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--lang', help='Language to generate manifest for.')
	parser.add_argument('--sample_dir', help='Sample directory to search for samples.')
	parser.add_argument('--output_dir', help='The directory to save the manifest file')
	parser.add_argument('--output_name', help='The name of the output file, excluding extensions.')

	args = parser.parse_args(sys.argv[2:])
	if args.lang not in ALL_LANGS:
		sys.exit("Unrecognized language.")
	if args.lang not in SUPPORTED_LANGS:
		sys.exit("Unsupported language.")

	if not os.path.isdir(args.sample_dir):
		sys.exit("Sample directory does not exist.")
	if not os.path.isdir(args.output_dir):
		try:
			os.mkdir(args.output_dir)
		except OSError:
			sys.exit("Failed to created output directory.")

	if args.output_name is None:
		sys.exit("Output file name not specified.")

	return args

def base_manifest():
	manifest = OrderedDict()
	manifest['version'] = 2
	manifest['sets'] = []
	return manifest

def python_manifest(sample_dir):
	manifest = base_manifest()
	py_environment = OrderedDict()
	py_environment['bin'] = 'python3'
	py_environment['path'] = sample_dir
	py_environment['__items__'] = path_sample_pairs(sample_dir)
	manifest['sets'].append(py_environment)
	return manifest


def path_sample_pairs(sample_dir):
	items = []
	for root, dirs, files in os.walk(sample_dir):
		for file in files:
			items.append({
				'path': file,
				'sample': get_region_tag(os.path.join(root, file))
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

def dump(manifest, output_dir, output_name):
	Dumper.add_representer(OrderedDict, dict_representer)
	Dumper.add_representer(str,
                       SafeRepresenter.represent_str)

	with open(os.path.join(output_dir, '{}.manifest.yaml'.format(output_name)), 'w') as output_file:
			yaml.dump(manifest, output_file, Dumper=Dumper, default_flow_style=False)


if __name__ == '__main__':
	main()

