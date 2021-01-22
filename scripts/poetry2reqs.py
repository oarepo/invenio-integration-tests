#!/usr/bin/env python

# See https://github.com/sdispater/poetry/issues/100
import tomlkit
with open('poetry.lock') as t:
	lock = tomlkit.parse(t.read())
	for p in lock['package']:
		if not p['category'] == 'dev':
			print(f"{p['name']}=={p['version']}")
