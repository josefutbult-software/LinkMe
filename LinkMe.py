#!/bin/python3

import os
import argparse
import shutil
import pathlib
import json
import markdown
import re

LINKME_DIRNAME = '.LinkMe'
LINKME_BUILD_DIRNAME = 'build'
LINKME_DOCS_NAME = 'docs'

def main():
	parser = argparse.ArgumentParser(description='LinkMe is a tool to make documentation for a project')

	parser.add_argument('-i', '--init', type=str, nargs='?', const='./', help='Initialize the LinkMe project. Uses current directory as root if no path is specified.')
	parser.add_argument('-b', '--build', type=str, nargs='?', const='./', help='Build LinkMe project. Uses current directory as root if no path is specified.')
	parser.add_argument('-in', '--input', type=str, help='Select input file for initialization or building. Uses file specified at init if not specified.')
	parser.add_argument('-o', '--output', type=str, help='Select output file for initialization or building. Uses file specified at init if not specified.')
	parser.add_argument('-f', '--force', action='store_true', help='Force reinitialization/building of LinkMe project')
	args = parser.parse_args()
	
	if args.init:
		init(args.init, args.force, args.input, args.output)

	elif args.build:
		build(args.build, args.input, args.output)


def init(filepath, force, input_file, output_file):

	if filepath != './':
		filepath = os.path.abspath(filepath)


	if os.path.isdir(filepath):
		try:
			os.mkdir(os.path.join(filepath, LINKME_DIRNAME))
		except FileExistsError:
			if force:
				shutil.rmtree(os.path.join(filepath, LINKME_DIRNAME), ignore_errors=True)
				try:
					os.mkdir(os.path.join(filepath, LINKME_DIRNAME))
				except FileExistsError:
					print(f"Unable to create {LINKME_DIRNAME} directory. Check if you have the correct privileges.")
					exit()
			else:
				print(f"A LinkMe project has already been initialized {'in ' + filepath if filepath != './' else 'here'}. Use --force to reinitialize it.")
				exit()
		
		print(f"Initializing LinkMe project {'in ' + filepath if filepath != './' else ''}")

		try:
			os.mkdir(os.path.join(filepath, LINKME_DIRNAME, LINKME_BUILD_DIRNAME))
		except FileExistsError:
			print(f"Unable to create {LINKME_BUILD_DIRNAME} directory. Check if you have the correct privileges.")
			exit()

	else:
		print(f"{filepath} is not a correct filepath.")
		exit()

	with open(path_relative_script_dir('project-template.json'), 'r') as template_file:
		project = json.loads(template_file.read())

	project['build_dir'] = os.path.abspath(os.path.join(filepath, LINKME_DIRNAME, LINKME_BUILD_DIRNAME))

	if not input_file or not output_file:
		if not os.path.isdir(os.path.join(filepath, LINKME_DOCS_NAME)):
			os.mkdir(os.path.join(filepath, LINKME_DOCS_NAME))

	if not input_file:
		shutil.copyfile(path_relative_script_dir('example_input.md'), os.path.join(filepath, LINKME_DOCS_NAME, 'example.md'))
		input_file = os.path.join(filepath, LINKME_DOCS_NAME, 'example.md')

	if not output_file:
		output_file = os.path.join(filepath, LINKME_DIRNAME, LINKME_BUILD_DIRNAME, 'build.html')

	project['input'] = os.path.abspath(input_file)
	project['output'] = os.path.abspath(output_file) if output_file else ''

	with open(os.path.join(filepath, LINKME_DIRNAME, 'project.json'), 'x') as file:
		file.write(json.dumps(project, sort_keys=True, indent=4))


def build(root_dir, input_file, output_file):

	if root_dir != './':
		root_dir = os.path.abspath(root_dir)

	if not os.path.isdir(os.path.join(root_dir, LINKME_DIRNAME)):
		print(f"{root_dir if root_dir != './' else 'This directory'} is not initialized as a LinkMe project. Run \"LinkMe --init\" to initialize.")
		exit()

	with open(os.path.join(root_dir, LINKME_DIRNAME, 'project.json'), 'r') as file:
		project = json.loads(file.read())

	if not input_file:
		input_file = project['input']

	if not output_file:	
		output_file = project['output']

	with open(input_file) as raw:
		parsed_doc = parse(raw.read(), root_dir)

	print(parsed_doc)
	with open(output_file, 'w+') as out:
		out.write(parsed_doc)

def format_tag(text):
	formated = text.split(' ')
	filepath, snippet = formated[0].split(':')[:2]

	args = {}
	for instance in formated[1:]:
		try:
			name, variable = instance.split('=')[:2]
			args[name] = variable
		except ValueError:
			pass
		except AttributeError:
			pass

	return filepath, snippet, args


def substitute_codeblock(text, root_dir):
	match = re.search(r'{! CODEBLOCK (.*?)!}', text)
	if match:
		
		filepath, snippet, args = format_tag(match.groups(1)[0])

		if args['margin']:
			top_margin, bottom_margin = [int(i) for i in args['margin'].split(':')]

		with open(os.path.join(root_dir, os.path.join(*filepath.split('/')))) as code_file:
			lines = code_file.read().split('\n')
			res = filter(lambda line: snippet in line, lines)
			for instance in res:
				code_block = lines[max(0, lines.index(instance) - top_margin):min(len(lines), lines.index(instance) + bottom_margin)]
				text_block = '```python\n' + '\n'.join(code_block) + '\n```\n'
				try:
					return f"{args['heading']}\n{text_block}"
				except KeyError:
					return text_block

	return f"{text}\n"


def parse(raw, root_dir):
	output = ''
	for line in raw.split('\n'):
		output += substitute_codeblock(line, root_dir)
	return markdown.markdown(output, extensions=['fenced_code'])


def path_relative_script_dir(path):
	return os.path.join(pathlib.Path(__file__).parent.resolve(), path)


if __name__ == '__main__':
	main()