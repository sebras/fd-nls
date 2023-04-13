#!/usr/bin/python3

import unittest

from difflib import unified_diff
from pathlib import Path
from shutil import copy

import codec_mazovia

PROJECTS = (
    "append",
    "assign",
    "blocek",
    "choice",
    "compute",
    "ctmouse",
    "diskcopy",
    "display",
    "doslfn",
    "dosshell",
    "dosutil",
    "edict",
    "edlin",
    "exe2bin",
    "fc",
    "fdhelper",
    "fdi",
    "fdimples",
    "fdisk",
    "fdi-x86",
    "fdnet",
    "fdnpkg",
    "fdpkg",
    "fdshell",
    "fdtui",
    "find",
    "flashrom",
    "freecom",
    "gcdrom",
    "help-legacy",
    "htmlhelp",
    "label",
    "localize",
    "md5sum",
    "mem",
    "mirror",
    "mkeyb",
    "mode",
    "more",
    "move",
    "nlsfunc",
    "packages",
    "password",
    "pause",
    "pdtree",
    "pgme",
    "pkgtools",
    "runtime",
    "share",
    "slicer",
    "sort",
    "stamp",
    "syslnx",
    "tee",
    "test.out",
    "trch",
    "tree",
    "usbdos",
    "v8power",
    "vmsmount",
    "wget",
    "xcopy",
    "xdel",
)

LANGUAGES = {
    "en": "CP437",
    "br": "CP850",  # Only CTMOUSE uses 'br' for Brazilian Portuguese
    "cz": "CP852",  # Czech language code is really 'cs' (ISO 639-1)
    "da": "CP850",
    "de": "CP850",
    "dk": "CP850",  # Actually we really should be using 'da' not 'dk'
    "eo": None,     # Esperanto??
    "es": "CP850",
    "eu": None,     # Basque maybe CP850?
    "fi": "CP850",
    "fr": "CP850",
    "hu": "CP852",
    "is": "CP850",  # Icelandic
    "it": "CP850",
    "ja": None,     # Unknown target encoding, doesn't it need DBCS support everywhere?
    "la": None,     # Latin??
    "lv": "CP775",
    "nl": "CP850",
    "no": "CP865",
    "pl": "mazovia", # our local implementation
    "pt": "CP850",
    "ptBR": "CP850", # name will be truncated in _output
    "rs": "CP852",
    "ru": "CP866",
    "si": "CP852",  # Slovene (but only fdnpkg uses it, others use 'sl')
    "sk": None,     # Unknown (but only used by htmlhelp)
    "sl": "CP852",
    "sv": "CP850",
    "tr": "CP857",
    "ua": "CP866",
}


output = Path("_output")

HDR = """\
## This file is autogenerated, any updates will be lost. Please visit
## https://github.com/shidel/fd-nls to update the UTF-8 version of it.
##
"""


class Kitten(unittest.TestCase):

    top = Path('.')

    def _dotest(self, tipo, prg, lng):

        indir = self.top / prg / tipo
        if not indir.is_dir():
            self.skipTest("'%s' not found" % str(indir))

        outdir = output / prg / tipo
        outdir.mkdir(parents=True, exist_ok=True)

        # Hack for Brazilian (.ptBR -> .ptb)
        tgt = outdir / (prg + "." + lng[0:4].lower())

        src_utf = indir / (prg + "." + lng + ".UTF-8")
        src_cpg = indir / (prg + "." + lng)

        # Ensure UTF-8 source is valid if it exists
        have_utf = False
        try:
            txt = src_utf.read_text(encoding="UTF-8")
            have_utf = True
        except FileNotFoundError:
            pass
        except UnicodeDecodeError as e:
            msg = "invalid character in UTF-8 ('%s')" % e
            raise self.failureException(msg) from None

        if have_utf:
            # Convert to output codepade
            try:
                hdr = HDR if tipo == 'nls' else HDR.replace('#', ';')
                tgt.write_text(hdr + txt, encoding=LANGUAGES[lng], newline='\r\n')
            except UnicodeEncodeError as e:
                msg = "invalid character for target codepage ('%s')" % e
                raise self.failureException(msg) from None

            # Compare encoded text file against our converted text
            try:
                txt_cpg = src_cpg.read_text(encoding=LANGUAGES[lng])
                if txt_cpg != txt:
                    txt_list = txt.split('\n')
                    cpg_list = txt_cpg.split('\n')
                    diff = unified_diff(txt_list, cpg_list, fromfile=str(src_utf), tofile=str(src_cpg), lineterm='\n')
                    msg = "UTF-8 and encoded text differ\n%s" % '\n'.join(diff)
                    raise self.failureException(msg) from None
            except FileNotFoundError:
                pass

        else:
            # Very little we can check on encoded text, just copy it to
            # the output directory.
            try:
                copy(src_cpg, outdir)
            except FileNotFoundError:
                self.skipTest("'%s' not found" % lng)


def generate_kitten_tests():
    def create_test(test):
        def do_test(self):
            self._dotest(*test)

        docstring = """Kitten %s (%s) [%s]""" % (test[0].upper(), test[1], test[2].upper())
        setattr(do_test, '__doc__', docstring)
        return do_test

    # Insert each test into the testcase
    tests = []
    for p in PROJECTS:
        for l in LANGUAGES.keys():
            nls = Path(p) / 'nls'
            if nls.is_dir():
                tests.append(('nls', p, l))

            hlp = Path(p) / 'help'
            if hlp.is_dir():
                tests.append(('help', p, l))

    for test in tests:
        setattr(Kitten, 'test_%s_%s_%s' % test, create_test(test))


class MyTestResult(unittest.TextTestResult):

    def getDescription(self, test):
        return '%-80s' % test.shortDescription()


class MyTestRunner(unittest.TextTestRunner):
    resultclass = MyTestResult


if __name__ == '__main__':
    generate_kitten_tests()

    unittest.main(testRunner=MyTestRunner, verbosity=2)
