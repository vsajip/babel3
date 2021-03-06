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

"""Writing of files in the ``gettext`` MO (machine object) format.

:since: version 0.9
:see: `The Format of MO Files
       <http://www.gnu.org/software/gettext/manual/gettext.html#MO-Files>`_
"""
from __future__ import unicode_literals

import array
import struct

from babel.compat import long_type, xrange, PY3
from babel.messages.catalog import Catalog, Message

__all__ = ['read_mo', 'write_mo']
__docformat__ = 'restructuredtext en'


LE_MAGIC = long_type(0x950412de)
BE_MAGIC = long_type(0xde120495)

def read_mo(fileobj):
    """Read a binary MO file from the given file-like object and return a
    corresponding `Catalog` object.

    :param fileobj: the file-like object to read the MO file from
    :return: a catalog object representing the parsed MO file
    :rtype: `Catalog`

    :note: The implementation of this function is heavily based on the
           ``GNUTranslations._parse`` method of the ``gettext`` module in the
           standard library.
    """
    catalog = Catalog()
    headers = {}

    filename = getattr(fileobj, 'name', '')

    buf = fileobj.read()
    buflen = len(buf)
    unpack = struct.unpack

    # Parse the .mo file header, which consists of 5 little endian 32
    # bit words.
    magic = unpack('<I', buf[:4])[0] # Are we big endian or little endian?
    if magic == LE_MAGIC:
        version, msgcount, origidx, transidx = unpack('<4I', buf[4:20])
        ii = '<II'
    elif magic == BE_MAGIC:
        version, msgcount, origidx, transidx = unpack('>4I', buf[4:20])
        ii = '>II'
    else:
        raise IOError(0, 'Bad magic number', filename)

    # Now put all messages from the .mo file buffer into the catalog
    # dictionary
    for i in xrange(0, msgcount):
        mlen, moff = unpack(ii, buf[origidx:origidx + 8])
        mend = moff + mlen
        tlen, toff = unpack(ii, buf[transidx:transidx + 8])
        tend = toff + tlen
        if mend < buflen and tend < buflen:
            msg = buf[moff:mend]
            tmsg = buf[toff:tend]
        else:
            raise IOError(0, 'File is corrupt', filename)

        # See if we're looking at GNU .mo conventions for metadata
        if mlen == 0:
            # Catalog description
            lastkey = key = None
            for item in tmsg.splitlines():
                item = item.strip()
                if not item:
                    continue
                if b':' in item:
                    key, value = item.split(b':', 1)
                    lastkey = key = key.strip().lower()
                    headers[key] = value.strip()
                elif lastkey:
                    headers[lastkey] += '\n' + item

        if b'\x04' in msg: # context
            ctxt, msg = msg.split(b'\x04')
        else:
            ctxt = None

        if b'\x00' in msg: # plural forms
            msg = msg.split(b'\x00')
            tmsg = tmsg.split(b'\x00')
            if catalog.charset:
                msg = [x.decode(catalog.charset) for x in msg]
                tmsg = [x.decode(catalog.charset) for x in tmsg]
        else:
            if catalog.charset:
                msg = msg.decode(catalog.charset)
                tmsg = tmsg.decode(catalog.charset)
        catalog[msg] = Message(msg, tmsg, context=ctxt)

        # advance to next entry in the seek tables
        origidx += 8
        transidx += 8

    catalog.mime_headers = list(headers.items())
    return catalog

def write_mo(fileobj, catalog, use_fuzzy=False):
    """Write a catalog to the specified file-like object using the GNU MO file
    format.

    >>> from babel.messages import Catalog
    >>> from babel.compat import BytesIO, GNUTranslations

    >>> catalog = Catalog(locale='en_US')
    >>> catalog.add('foo', 'Voh')
    <Message ...>
    >>> catalog.add(('bar', 'baz'), ('Bahr', 'Batz'))
    <Message ...>
    >>> catalog.add('fuz', 'Futz', flags=['fuzzy'])
    <Message ...>
    >>> catalog.add('Fizz', '')
    <Message ...>
    >>> catalog.add(('Fuzz', 'Fuzzes'), ('', ''))
    <Message ...>
    >>> buf = BytesIO()
    >>> write_mo(buf, catalog)
    >>> _ = buf.seek(0)
    >>> translations = GNUTranslations(fp=buf)
    >>> translations.ugettext('foo') == 'Voh'
    True
    >>> translations.ungettext('bar', 'baz', 1) == 'Bahr'
    True
    >>> translations.ungettext('bar', 'baz', 2) == 'Batz'
    True
    >>> translations.ugettext('fuz') == 'fuz'
    True
    >>> translations.ugettext('Fizz') == 'Fizz'
    True
    >>> translations.ugettext('Fuzz') == 'Fuzz'
    True
    >>> translations.ugettext('Fuzzes') == 'Fuzzes'
    True

    :param fileobj: the file-like object to write to
    :param catalog: the `Catalog` instance
    :param use_fuzzy: whether translations marked as "fuzzy" should be included
                      in the output
    """
    messages = list(catalog)
    if not use_fuzzy:
        messages[1:] = [m for m in messages[1:] if not m.fuzzy]
    messages.sort()

    ids = strs = b''
    offsets = []

    for message in messages:
        # For each string, we need size and file offset.  Each string is NUL
        # terminated; the NUL does not count into the size.
        if message.pluralizable:
            msgid = b'\x00'.join([
                msgid.encode(catalog.charset) for msgid in message.id
            ])
            msgstrs = []
            for idx, string in enumerate(message.string):
                if not string:
                    msgstrs.append(message.id[min(int(idx), 1)])
                else:
                    msgstrs.append(string)
            msgstr = b'\x00'.join([
                msgstr.encode(catalog.charset) for msgstr in msgstrs
            ])
        else:
            msgid = message.id.encode(catalog.charset)
            if not message.string:
                msgstr = message.id.encode(catalog.charset)
            else:
                msgstr = message.string.encode(catalog.charset)
        if message.context:
            msgid = b'\x04'.join([message.context.encode(catalog.charset),
                                 msgid])
        offsets.append((len(ids), len(msgid), len(strs), len(msgstr)))
        ids += msgid + b'\x00'
        strs += msgstr + b'\x00'

    # The header is 7 32-bit unsigned integers.  We don't use hash tables, so
    # the keys start right after the index tables.
    keystart = 7 * 4 + 16 * len(messages)
    valuestart = keystart + len(ids)

    # The string table first has the list of keys, then the list of values.
    # Each entry has first the size of the string, then the file offset.
    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    offsets = koffsets + voffsets

    fileobj.write(struct.pack(str('Iiiiiii'),
        LE_MAGIC,                   # magic
        0,                          # version
        len(messages),              # number of entries
        7 * 4,                      # start of key index
        7 * 4 + len(messages) * 8,  # start of value index
        0, 0                        # size and offset of hash table
    ))
    if PY3:
        fileobj.write(array.array("i", offsets).tobytes())
    else:
        fileobj.write(array.array(str("i"), offsets).tostring())
    fileobj.write(ids + strs)
