# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://babel.edgewall.org/wiki/License.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://babel.edgewall.org/log/.

from datetime import datetime
from distutils.dist import Distribution
from distutils.errors import DistutilsOptionError
from distutils.log import _global_log
import doctest
import logging
import os
import shutil
import sys
import time
import unittest

from babel import __version__ as VERSION
from babel.compat import StringIO
from babel.dates import format_datetime
from babel.messages import frontend
from babel.util import LOCALTZ
from babel.messages.pofile import read_po


this_dir = os.path.abspath(os.path.dirname(__file__))

class CompileCatalogTestCase(unittest.TestCase):

    def setUp(self):
        self.olddir = os.getcwd()
        self.datadir = os.path.join(this_dir, 'data')
        os.chdir(self.datadir)
        _global_log.threshold = 5 # shut up distutils logging

        self.dist = Distribution(dict(
            name='TestProject',
            version='0.1',
            packages=['project']
        ))
        self.cmd = frontend.compile_catalog(self.dist)
        self.cmd.initialize_options()

    def tearDown(self):
        os.chdir(self.olddir)

    def test_no_directory_or_output_file_specified(self):
        self.cmd.locale = 'en_US'
        self.cmd.input_file = 'dummy'
        self.assertRaises(DistutilsOptionError, self.cmd.finalize_options)

    def test_no_directory_or_input_file_specified(self):
        self.cmd.locale = 'en_US'
        self.cmd.output_file = 'dummy'
        self.assertRaises(DistutilsOptionError, self.cmd.finalize_options)


class ExtractMessagesTestCase(unittest.TestCase):

    def setUp(self):
        self.olddir = os.getcwd()
        self.datadir = os.path.join(this_dir, 'data')
        os.chdir(self.datadir)
        _global_log.threshold = 5 # shut up distutils logging

        self.dist = Distribution(dict(
            name='TestProject',
            version='0.1',
            packages=['project']
        ))
        self.cmd = frontend.extract_messages(self.dist)
        self.cmd.initialize_options()

    def tearDown(self):
        pot_file = self._pot_file()
        if os.path.isfile(pot_file):
            os.unlink(pot_file)

        os.chdir(self.olddir)

    def  _i18n_dir(self):
        return os.path.join(self.datadir, 'project', 'i18n')

    def _pot_file(self):
        return os.path.join(self._i18n_dir(), 'temp.pot')

    def assert_pot_file_exists(self):
        assert os.path.isfile(self._pot_file())

    def test_neither_default_nor_custom_keywords(self):
        self.cmd.output_file = 'dummy'
        self.cmd.no_default_keywords = True
        self.assertRaises(DistutilsOptionError, self.cmd.finalize_options)

    def test_no_output_file_specified(self):
        self.assertRaises(DistutilsOptionError, self.cmd.finalize_options)

    def test_both_sort_output_and_sort_by_file(self):
        self.cmd.output_file = 'dummy'
        self.cmd.sort_output = True
        self.cmd.sort_by_file = True
        self.assertRaises(DistutilsOptionError, self.cmd.finalize_options)

    def test_input_dirs_is_treated_as_list(self):
        self.cmd.input_dirs = self.datadir
        self.cmd.output_file = self._pot_file()
        self.cmd.finalize_options()
        self.cmd.run()
        
        catalog = read_po(open(self._pot_file(), 'U'))
        msg = catalog.get('bar')
        self.assertEqual(1, len(msg.locations))
        self.assertTrue('file1.py' in msg.locations[0][0])

    def test_input_dirs_handle_spaces_after_comma(self):
        self.cmd.input_dirs = 'foo,  bar'
        self.cmd.output_file = self._pot_file()
        self.cmd.finalize_options()
        
        self.assertEqual(['foo', 'bar'], self.cmd.input_dirs)

    def test_extraction_with_default_mapping(self):
        self.cmd.copyright_holder = 'FooBar, Inc.'
        self.cmd.msgid_bugs_address = 'bugs.address@email.tld'
        self.cmd.output_file = 'project/i18n/temp.pot'
        self.cmd.add_comments = 'TRANSLATOR:,TRANSLATORS:'

        self.cmd.finalize_options()
        self.cmd.run()

        self.assert_pot_file_exists()

        self.assertEqual(
r"""# Translations template for TestProject.
# Copyright (C) %(year)s FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, %(year)s.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: %(date)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. TRANSLATOR: This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

#: project/ignored/this_wont_normally_be_here.py:11
msgid "FooBar"
msgid_plural "FooBars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'year': time.strftime('%Y'),
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
        open(self._pot_file(), 'U').read())

    def test_extraction_with_mapping_file(self):
        self.cmd.copyright_holder = 'FooBar, Inc.'
        self.cmd.msgid_bugs_address = 'bugs.address@email.tld'
        self.cmd.mapping_file = 'mapping.cfg'
        self.cmd.output_file = 'project/i18n/temp.pot'
        self.cmd.add_comments = 'TRANSLATOR:,TRANSLATORS:'

        self.cmd.finalize_options()
        self.cmd.run()

        self.assert_pot_file_exists()

        self.assertEqual(
r"""# Translations template for TestProject.
# Copyright (C) %(year)s FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, %(year)s.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: %(date)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. TRANSLATOR: This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'year': time.strftime('%Y'),
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
        open(self._pot_file(), 'U').read())

    def test_extraction_with_mapping_dict(self):
        self.dist.message_extractors = {
            'project': [
                ('**/ignored/**.*', 'ignore',   None),
                ('**.py',           'python',   None),
            ]
        }
        self.cmd.copyright_holder = 'FooBar, Inc.'
        self.cmd.msgid_bugs_address = 'bugs.address@email.tld'
        self.cmd.output_file = 'project/i18n/temp.pot'
        self.cmd.add_comments = 'TRANSLATOR:,TRANSLATORS:'

        self.cmd.finalize_options()
        self.cmd.run()

        self.assert_pot_file_exists()

        self.assertEqual(
r"""# Translations template for TestProject.
# Copyright (C) %(year)s FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, %(year)s.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: %(date)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. TRANSLATOR: This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'year': time.strftime('%Y'),
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
        open(self._pot_file(), 'U').read())


class InitCatalogTestCase(unittest.TestCase):

    def setUp(self):
        self.olddir = os.getcwd()
        self.datadir = os.path.join(this_dir, 'data')
        os.chdir(self.datadir)
        _global_log.threshold = 5 # shut up distutils logging

        self.dist = Distribution(dict(
            name='TestProject',
            version='0.1',
            packages=['project']
        ))
        self.cmd = frontend.init_catalog(self.dist)
        self.cmd.initialize_options()

    def tearDown(self):
        for dirname in ['en_US', 'ja_JP', 'lv_LV']:
            locale_dir = os.path.join(self._i18n_dir(), dirname)
            if os.path.isdir(locale_dir):
                shutil.rmtree(locale_dir)

        os.chdir(self.olddir)

    def  _i18n_dir(self):
        return os.path.join(self.datadir, 'project', 'i18n')

    def _po_file(self, locale):
        return os.path.join(self._i18n_dir(), locale, 'LC_MESSAGES', 
                            'messages.po')

    def test_no_input_file(self):
        self.cmd.locale = 'en_US'
        self.cmd.output_file = 'dummy'
        self.assertRaises(DistutilsOptionError, self.cmd.finalize_options)

    def test_no_locale(self):
        self.cmd.input_file = 'dummy'
        self.cmd.output_file = 'dummy'
        self.assertRaises(DistutilsOptionError, self.cmd.finalize_options)

    def test_with_output_dir(self):
        self.cmd.input_file = 'project/i18n/messages.pot'
        self.cmd.locale = 'en_US'
        self.cmd.output_dir = 'project/i18n'

        self.cmd.finalize_options()
        self.cmd.run()

        po_file = self._po_file('en_US')
        assert os.path.isfile(po_file)

        self.assertEqual(
r"""# English (United States) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: en_US <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
       open(po_file, 'U').read())

    def test_keeps_catalog_non_fuzzy(self):
        self.cmd.input_file = 'project/i18n/messages_non_fuzzy.pot'
        self.cmd.locale = 'en_US'
        self.cmd.output_dir = 'project/i18n'

        self.cmd.finalize_options()
        self.cmd.run()

        po_file = self._po_file('en_US')
        assert os.path.isfile(po_file)

        self.assertEqual(
r"""# English (United States) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: en_US <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
       open(po_file, 'U').read())

    def test_correct_init_more_than_2_plurals(self):
        self.cmd.input_file = 'project/i18n/messages.pot'
        self.cmd.locale = 'lv_LV'
        self.cmd.output_dir = 'project/i18n'

        self.cmd.finalize_options()
        self.cmd.run()

        po_file = self._po_file('lv_LV')
        assert os.path.isfile(po_file)

        self.assertEqual(
r"""# Latvian (Latvia) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: lv_LV <LL@li.org>\n"
"Plural-Forms: nplurals=3; plural=(n%%10==1 && n%%100!=11 ? 0 : n != 0 ? 1 :"
" 2)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""
msgstr[2] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
       open(po_file, 'U').read())

    def test_correct_init_singular_plural_forms(self):
        self.cmd.input_file = 'project/i18n/messages.pot'
        self.cmd.locale = 'ja_JP'
        self.cmd.output_dir = 'project/i18n'

        self.cmd.finalize_options()
        self.cmd.run()

        po_file = self._po_file('ja_JP')
        assert os.path.isfile(po_file)

        self.assertEqual(
r"""# Japanese (Japan) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: ja_JP <LL@li.org>\n"
"Plural-Forms: nplurals=1; plural=0\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='ja_JP')},
       open(po_file, 'U').read())
   
    def test_supports_no_wrap(self):
        self.cmd.input_file = 'project/i18n/long_messages.pot'
        self.cmd.locale = 'en_US'
        self.cmd.output_dir = 'project/i18n'
        
        long_message = '"'+ 'xxxxx '*15 + '"'
        
        pot_contents = open('project/i18n/messages.pot', 'U').read()
        pot_with_very_long_line = pot_contents.replace('"bar"', long_message)
        open(self.cmd.input_file, 'w').write(pot_with_very_long_line)
        self.cmd.no_wrap = True

        self.cmd.finalize_options()
        self.cmd.run()

        po_file = self._po_file('en_US')
        assert os.path.isfile(po_file)
        self.assertEqual(
r"""# English (United States) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
# 
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: en_US <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid %(long_message)s
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en_US'),
       'long_message': long_message},
       open(po_file, 'U').read())
   
    def test_supports_width(self):
        self.cmd.input_file = 'project/i18n/long_messages.pot'
        self.cmd.locale = 'en_US'
        self.cmd.output_dir = 'project/i18n'
        
        long_message = '"'+ 'xxxxx '*15 + '"'
        
        pot_contents = open('project/i18n/messages.pot', 'U').read()
        pot_with_very_long_line = pot_contents.replace('"bar"', long_message)
        open(self.cmd.input_file, 'w').write(pot_with_very_long_line)
        self.cmd.width = 120
        self.cmd.finalize_options()
        self.cmd.run()

        po_file = self._po_file('en_US')
        assert os.path.isfile(po_file)
        self.assertEqual(
r"""# English (United States) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: en_US <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid %(long_message)s
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en_US'),
       'long_message': long_message},
       open(po_file, 'U').read())


class CommandLineInterfaceTestCase(unittest.TestCase):

    def setUp(self):
        self.datadir = os.path.join(this_dir, 'data')
        self.orig_working_dir = os.getcwd()
        self.orig_argv = sys.argv
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        sys.argv = ['pybabel']
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        os.chdir(self.datadir)
        
        self._remove_log_handlers()
        self.cli = frontend.CommandLineInterface()

    def tearDown(self):
        os.chdir(self.orig_working_dir)
        sys.argv = self.orig_argv
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr
        for dirname in ['lv_LV', 'ja_JP']: 
            locale_dir = os.path.join(self._i18n_dir(), dirname)
            if os.path.isdir(locale_dir):
                shutil.rmtree(locale_dir)
        self._remove_log_handlers()

    def _remove_log_handlers(self):
        # Logging handlers will be reused if possible (#227). This breaks the 
        # implicit assumption that our newly created StringIO for sys.stderr 
        # contains the console output. Removing the old handler ensures that a
        # new handler with our new StringIO instance will be used.
        log = logging.getLogger('babel')
        for handler in log.handlers:
            log.removeHandler(handler)

    def test_usage(self):
        try:
            self.cli.run(sys.argv)
            self.fail('Expected SystemExit')
        except SystemExit as e:
            self.assertEqual(2, e.code)
            self.assertEqual("""\
usage: pybabel command [options] [args]

pybabel: error: no valid command or option passed. try the -h/--help option for more information.
""", sys.stderr.getvalue().lower())

    def _run_init_catalog(self):
        i18n_dir = os.path.join(self.datadir, 'project', 'i18n')
        pot_path = os.path.join(self.datadir, 'project', 'i18n', 'messages.pot')
        init_argv = sys.argv + ['init', '--locale', 'en_US', '-d', i18n_dir,
                                '-i', pot_path]
        self.cli.run(init_argv)

    def test_no_duplicated_output_for_multiple_runs(self):
        self._run_init_catalog()
        first_output = sys.stderr.getvalue()
        self._run_init_catalog()
        second_output = sys.stderr.getvalue()[len(first_output):]
        
        # in case the log message is not duplicated we should get the same 
        # output as before
        self.assertEqual(first_output, second_output)

    def test_frontend_can_log_to_predefined_handler(self):
        custom_stream = StringIO()
        log = logging.getLogger('babel')
        log.addHandler(logging.StreamHandler(custom_stream))
        
        self._run_init_catalog()
        self.assertNotEqual(id(sys.stderr), id(custom_stream))
        self.assertEqual('', sys.stderr.getvalue())
        assert len(custom_stream.getvalue()) > 0

    def test_help(self):
        try:
            self.cli.run(sys.argv + ['--help'])
            self.fail('Expected SystemExit')
        except SystemExit as e:
            self.assertEqual(0, e.code)
            self.assertEqual("""\
usage: pybabel command [options] [args]

options:
  --version       show program's version number and exit
  -h, --help      show this help message and exit
  --list-locales  print all known locales and exit
  -v, --verbose   print as much as possible
  -q, --quiet     print as little as possible

commands:
  compile  compile message catalogs to mo files
  extract  extract messages from source files and generate a pot file
  init     create new message catalogs from a pot file
  update   update existing message catalogs from a pot file
""", sys.stdout.getvalue().lower())

    def _pot_file(self):
        return os.path.join(self._i18n_dir(), 'temp.pot')

    def assert_pot_file_exists(self):
        assert os.path.isfile(self._pot_file())

    def test_extract_with_default_mapping(self):
        pot_file = self._pot_file()
        self.cli.run(sys.argv + ['extract',
            '--copyright-holder', 'FooBar, Inc.',
            '--project', 'TestProject', '--version', '0.1',
            '--msgid-bugs-address', 'bugs.address@email.tld',
            '-c', 'TRANSLATOR', '-c', 'TRANSLATORS:',
            '-o', pot_file, 'project'])
        self.assert_pot_file_exists()
        self.assertEqual(
r"""# Translations template for TestProject.
# Copyright (C) %(year)s FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, %(year)s.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: %(date)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. TRANSLATOR: This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

#: project/ignored/this_wont_normally_be_here.py:11
msgid "FooBar"
msgid_plural "FooBars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'year': time.strftime('%Y'),
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
       open(pot_file, 'U').read())

    def test_extract_with_mapping_file(self):
        pot_file = self._pot_file()
        self.cli.run(sys.argv + ['extract',
            '--copyright-holder', 'FooBar, Inc.',
            '--project', 'TestProject', '--version', '0.1',
            '--msgid-bugs-address', 'bugs.address@email.tld',
            '--mapping', os.path.join(self.datadir, 'mapping.cfg'),
            '-c', 'TRANSLATOR', '-c', 'TRANSLATORS:',
            '-o', pot_file, 'project'])
        self.assert_pot_file_exists()
        self.assertEqual(
r"""# Translations template for TestProject.
# Copyright (C) %(year)s FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, %(year)s.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: %(date)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. TRANSLATOR: This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'year': time.strftime('%Y'),
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
       open(pot_file, 'U').read())

    def test_init_with_output_dir(self):
        po_file = self._po_file('en_US')
        self.cli.run(sys.argv + ['init',
            '--locale', 'en_US',
            '-d', os.path.join(self._i18n_dir()),
            '-i', os.path.join(self._i18n_dir(), 'messages.pot')])
        assert os.path.isfile(po_file)
        self.assertEqual(
r"""# English (United States) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: en_US <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
       open(po_file, 'U').read())

    def  _i18n_dir(self):
        return os.path.join(self.datadir, 'project', 'i18n')

    def test_init_singular_plural_forms(self):
        po_file = self._po_file('ja_JP')
        self.cli.run(sys.argv + ['init',
            '--locale', 'ja_JP',
            '-d', os.path.join(self._i18n_dir()),
            '-i', os.path.join(self._i18n_dir(), 'messages.pot')])
        assert os.path.isfile(po_file)
        self.assertEqual(
r"""# Japanese (Japan) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: ja_JP <LL@li.org>\n"
"Plural-Forms: nplurals=1; plural=0\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
       open(po_file, 'U').read())
            
    def test_init_more_than_2_plural_forms(self):
        po_file = self._po_file('lv_LV')
        self.cli.run(sys.argv + ['init',
            '--locale', 'lv_LV',
            '-d', self._i18n_dir(),
            '-i', os.path.join(self._i18n_dir(), 'messages.pot')])
        assert os.path.isfile(po_file)
        self.assertEqual(
r"""# Latvian (Latvia) translations for TestProject.
# Copyright (C) 2007 FooBar, Inc.
# This file is distributed under the same license as the TestProject
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: TestProject 0.1\n"
"Report-Msgid-Bugs-To: bugs.address@email.tld\n"
"POT-Creation-Date: 2007-04-01 15:30+0200\n"
"PO-Revision-Date: %(date)s\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: lv_LV <LL@li.org>\n"
"Plural-Forms: nplurals=3; plural=(n%%10==1 && n%%100!=11 ? 0 : n != 0 ? 1 :"
" 2)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel %(version)s\n"

#. This will be a translator coment,
#. that will include several lines
#: project/file1.py:8
msgid "bar"
msgstr ""

#: project/file2.py:9
msgid "foobar"
msgid_plural "foobars"
msgstr[0] ""
msgstr[1] ""
msgstr[2] ""

""" % {'version': VERSION,
       'date': format_datetime(datetime.now(LOCALTZ), 'yyyy-MM-dd HH:mmZ',
                               tzinfo=LOCALTZ, locale='en')},
       open(po_file, 'U').read())

    def test_compile_catalog(self):
        po_file = self._po_file('de_DE')
        mo_file = po_file.replace('.po', '.mo')
        self.cli.run(sys.argv + ['compile',
            '--locale', 'de_DE',
            '-d', self._i18n_dir()])
        assert not os.path.isfile(mo_file), 'Expected no file at %r' % mo_file
        self.assertEqual("""\
catalog %r is marked as fuzzy, skipping
""" % (po_file), sys.stderr.getvalue())

    def test_compile_fuzzy_catalog(self):
        po_file = self._po_file('de_DE')
        mo_file = po_file.replace('.po', '.mo')
        try:
            self.cli.run(sys.argv + ['compile',
                '--locale', 'de_DE', '--use-fuzzy',
                '-d', self._i18n_dir()])
            assert os.path.isfile(mo_file)
            self.assertEqual("""\
compiling catalog %r to %r
""" % (po_file, mo_file), sys.stderr.getvalue())
        finally:
            if os.path.isfile(mo_file):
                os.unlink(mo_file)

    def _po_file(self, locale):
        return os.path.join(self._i18n_dir(), locale, 'LC_MESSAGES', 
                            'messages.po')

    def test_compile_catalog_with_more_than_2_plural_forms(self):
        po_file = self._po_file('ru_RU')
        mo_file = po_file.replace('.po', '.mo')
        try:
            self.cli.run(sys.argv + ['compile',
                '--locale', 'ru_RU', '--use-fuzzy',
                '-d', self._i18n_dir()])
            assert os.path.isfile(mo_file)
            self.assertEqual("""\
compiling catalog %r to %r
""" % (po_file, mo_file), sys.stderr.getvalue())
        finally:
            if os.path.isfile(mo_file):
                os.unlink(mo_file)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(frontend))
    suite.addTest(unittest.makeSuite(CompileCatalogTestCase))
    suite.addTest(unittest.makeSuite(ExtractMessagesTestCase))
    suite.addTest(unittest.makeSuite(InitCatalogTestCase))
    suite.addTest(unittest.makeSuite(CommandLineInterfaceTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
