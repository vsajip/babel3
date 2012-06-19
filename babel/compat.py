import sys

if sys.version_info[0] < 3:
    PY3 = False

    from StringIO import StringIO
    import io
    BytesIO = io.BytesIO
    text_type = unicode
    string_types = basestring,
    integer_types = (int, long)
    unichr = unichr

    import cPickle as pickle
    from UserDict import DictMixin

    def exec_(code, globs=None, locs=None):
        """Execute code in a namespace."""
        if globs is None:
            frame = sys._getframe(1)
            globs = frame.f_globals
            if locs is None:
                locs = frame.f_locals
            del frame
        elif locs is None:
            locs = globs
        exec("""exec code in globs, locs""")

    from itertools import izip
    from ConfigParser import RawConfigParser
    
    xrange = xrange

    from gettext import GNUTranslations
else:
    PY3 = True

    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO
    text_type = str
    string_types = str,
    integer_types = int,

    def unichr(s):
        return u(chr(s))

    import pickle
    from collections import UserDict as DictMixin

    exec_ = eval('exec')

    izip = zip
    from configparser import RawConfigParser

    xrange = range

    #import functools, traceback
    #sys.excepthook = functools.partial(traceback.print_exception, chain=False)

    from gettext import GNUTranslations

    GNUTranslations.ugettext = GNUTranslations.gettext
    GNUTranslations.ungettext = GNUTranslations.ngettext

long_type = integer_types[-1]

try:
    import threading
except ImportError:
    import dummy_threading as threading

