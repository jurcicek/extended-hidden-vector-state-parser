import os
import threading
import re
import codecs
import shutil
import warnings

from svc.egg import PythonEgg
from svc.utils import issequence
from subprocess import Popen, PIPE

PDT_ENCODING = 'iso-8859-2'

# Turn off warnings about using tmpnam()
warnings.filterwarnings('ignore', 'tmpnam.*', RuntimeWarning, r'.*\.pdt')

class FMAnalyzer(PythonEgg):
    """Full morphology analyzer

    Represents FMorph programs from Prague Dependecy Treebank
    """
    def __init__(self, fmorph_dir, fm_dict=None):
        """Create new FMAnalyzer

        `fmorph_dir` is directory, where FMorph is installed
        """
        self.fm_bin = os.path.join(fmorph_dir, 'FMAnalyze.pl')
        if fm_dict is None:
            self.fm_dict = os.path.join(fmorph_dir, 'CZE-a.il2')
        else:
            self.fm_dict = fm_dict

    def analyzeFileToFile(self, in_fn, out_fn):
        """Morphologicaly analyze file `in_fn`, store output in `out_fn`
        """
        p = Popen([self.fm_bin, 'NOSTDIO', in_fn, out_fn, self.fm_dict])
        p.wait()


class EXPTagger(PythonEgg):
    """Disambiguated morphology analyzer

    Represents EXPTagger program from Prague Dependecy Treebank
    """
    def __init__(self, expt_dir, guess=True):
        """Create new EXPTagger

        :Parameters:
            - `expt_dir` - directory, where EXPTagger is installed
            - `guess` - activate guessing mode (G cmdline flag), defaults to
              True
        """
        self.expt_dir = expt_dir
        self.expt_bin = os.path.join(expt_dir, 'CZ010619x')
        self.guess = guess

    def analyzeFileToFile(self, in_fn, out_fn):
        """Disambiguate morphologicaly analyzed file `in_fn`, store output in `out_fn`
        """
        cwd = os.getcwd()
        if not os.path.isabs(in_fn):
            in_fn = os.path.join(cwd, in_fn)
        if not os.path.isabs(out_fn):
            out_fn = os.path.join(cwd, out_fn)
        os.chdir(self.expt_dir)
        try:
            mode = 'T'
            if self.guess:
                mode += 'G'
            p = Popen([self.expt_bin, mode, in_fn, out_fn])
            p.wait()
        finally:
            os.chdir(cwd)


class PDTParser(PythonEgg):
    """Prague Dependency Treebank SGML-like format parser
    """
    _reWord = re.compile(r'(?mu)<(?P<type>f|d|D).*?>(?P<orig>.*?)(?P<rest><+.*)*$')
    _rePDTTag = re.compile(r'(?u)<M(?P<an_type>.)(?P<type>.).*?>(?P<content>(\w|[0-9]|-)*)')

    def parse(self, text):
        """Parse string `text`

        Return generator yielding 3-tuple (`orig`, `unique`, `tags`), where:
            - `orig` is original word
            - `unique` is 2-tuple (`uniq_lemma`, `uniq_tag`) representing
              disambiguated lemma and POS tag.
            - `tags` is list of 2-tuples (`lemma`, `l_tags`) where `l_tags` are
              possible POS tags corresponding to lemma
        """
        for match in self._reWord.finditer(text):
            uniq_lemma = None
            uniq_tag = None

            type = match.group('type')
            if type == 'D':
                yield None, (None, None), []
                continue

            orig = match.group('orig')

            if type == 'd':
                yield orig, (None, None), []
                continue

            rest = match.group('rest')

            tags = []
            for match in self._rePDTTag.finditer(rest):
                an_type = match.group('an_type')
                type = match.group('type')
                content = match.group('content')

                if type == 'l':
                    if '-' in content:
                        content = content[:content.index('-')]
                    content = content.strip('_')
                elif type == 't':
                    content += '-' * (15 - len(content))

                if an_type == 'M':
                    if type == 'l':
                        tags.append((content, []))
                    elif type == 't':
                        tags[-1][1].append(content)
                elif an_type == 'D':
                    if type == 'l':
                        uniq_lemma = content
                    elif type == 't':
                        uniq_tag = content
                else:
                    continue

            yield orig, (uniq_lemma, uniq_tag), tags

    def parseFile(self, fn, encoding=None):
        """Read file `fn` and parse output using parse()
        """
        if encoding is None:
            encoding = PDT_ENCODING
        fr = file(fn)
        try:
            input = fr.read().decode(encoding)
        finally:
            fr.close()
        return self.parse(input)


class Morphology(PythonEgg):
    def __init__(self, pdt20dir):
        super(Morphology, self).__init__()
        self.pdt20dir = pdt20dir
        self.tokenizer = os.path.join(pdt20dir, 'tokenizer/run_tokenizer')
        self.morphology = os.path.join(pdt20dir, 'morphology/run_morphology')

    def process(self, lines):
        parse_dn = os.tmpnam()
        token_dn = os.path.join(parse_dn, '1-token')
        morph_dn = os.path.join(parse_dn, '2-morph')
        input_fn = os.path.join(parse_dn, 'input')
        os.mkdir(parse_dn)
        NULL = file('/dev/null', 'w')
        try:
            os.mkdir(token_dn)
            os.mkdir(morph_dn)
            input_fw = codecs.open(input_fn, 'w', PDT_ENCODING)
            try:
                for line in lines:
                    input_fw.write(line + '\n')
            finally:
                input_fw.close()

            tokenizer = Popen([self.tokenizer, token_dn, input_fn], stdout=NULL, stderr=NULL)
            if tokenizer.wait() != 0:
                raise ValueError("Couldn't run PDT tokenizer")

            morphology = Popen([self.morphology, token_dn, morph_dn], stdout=NULL, stderr=NULL)
            if morphology.wait() != 0:
                raise ValueError("Couldn't run PDT morphology")

            input_base = os.path.splitext(os.path.basename(input_fn))[0]
            output_fn = os.path.join(morph_dn, input_base+'.csts')
            output_fr = codecs.open(output_fn, 'r', PDT_ENCODING)
            try:
                csts = output_fr.read()
            finally:
                output_fr.close()

            return csts
        finally:
            NULL.close()
            shutil.rmtree(parse_dn)            

class PDT20Parser(PythonEgg):
    """Prague Dependency Treebank v2.0 SGML-like format parser
    """
    _reWord = re.compile(r'(?mu)<(?P<type>f|d|D|s)(>|\s.*?>)(?P<orig>.*?)(?P<rest><+.*)*$')
    _rePDTTag = re.compile(r'(?u)<MD(?P<type>.).*?>(?P<content>(\w|[0-9]|-)*)')

    def parse(self, text):
        """Parse string `text`

        Return generator yielding 4-tuple (`orig`, `unique_lemma`,
        `unique_pos`, `uniq_analytic`).
        """
        for match in self._reWord.finditer(text):
            uniq_lemma = None
            uniq_tag = None
            uniq_analytic = None

            type = match.group('type')
            if type == 'D':
                yield None, None, None, None
                continue

            if type == 's':
                yield '<s>', None, None, None
                continue

            orig = match.group('orig')

            if type == 'd':
                yield orig, None, None, None
                continue

            rest = match.group('rest')

            tags = []
            for match in self._rePDTTag.finditer(rest):
                type = match.group('type')
                content = match.group('content')

                if type == 'l':
                    if '-' in content:
                        content = content[:content.index('-')]
                    uniq_lemma = content.strip('_')
                elif type == 't':
                    uniq_tag = content + '-' * (15 - len(content))
                elif type == 'A':
                    uniq_analytic = content
                else:
                    continue

            yield orig, uniq_lemma, uniq_tag, uniq_analytic

    def parseFile(self, fn, encoding=None):
        """Read file `fn` and parse output using parse()
        """
        if encoding is None:
            encoding = PDT_ENCODING
        fr = file(fn)
        try:
            input = fr.read().decode(encoding)
        finally:
            fr.close()
        return self.parse(input)

    def mapOutput(self, (lemma, pos, anl)):
        if None not in (lemma, pos) and pos[10] == 'N':
            lemma = 'ne' + lemma
        return lemma, pos, anl

    def split(self, csts):
        csts_base = os.path.splitext(csts)[0]
        fn_lemma = csts_base + '.lemma'
        fn_pos = csts_base + '.pos'
        fn_anl = csts_base + '.anl'

        fns = [csts_base + i for i in ['.lemma', '.pos', '.anl']]
        fws = [codecs.open(fn, 'w', 'utf-8') for fn in fns]

        try:
            line = []
            for p in self.parseFile(csts):
                orig = p[0]
                if orig == '<s>':
                    if not line:
                        # Doubled <s> tags
                        continue
                    to_write = [[] for i in fws]
                    for item in line:
                        for i, w in zip(item, to_write):
                            if i is None:
                                w.append('None')
                            else:
                                w.append(i)
                    for out_line, fw in zip(to_write, fws):
                        out_line = ' '.join(out_line) + '\n'
                        fw.write(out_line)

                    del line[:]
                else:
                    line.append(self.mapOutput(p[1:]))
            else:
                to_write = [[] for i in fws]
                for item in line:
                    for i, w in zip(item, to_write):
                        if i is None:
                            w.append('None')
                        else:
                            w.append(i)
                for out_line, fw in zip(to_write, fws):
                    out_line = ' '.join(out_line) + '\n'
                    fw.write(out_line)
        finally:
            [fw.close() for fw in fws]
