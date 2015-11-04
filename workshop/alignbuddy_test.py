#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# NOTE: BioPython 16.6+ required.

"""
This program is free software in the public domain as stipulated by the Copyright Law
of the United States of America, chapter 1, subsection 105. You may modify it and/or redistribute it
without restriction.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

name: alignbuddy_tests.py
version: 1, alpha
author: Stephen R. Bond
email: steve.bond@nih.gov
institute: Computational and Statistical Genomics Branch, Division of Intramural Research,
           National Human Genome Research Institute, National Institutes of Health
           Bethesda, MD
repository: https://github.com/biologyguy/BuddySuite
© license: None, this work is public domain

Description: Collection of PyTest unit tests for the AlignBuddy.py program
"""

import pytest
from hashlib import md5
import os
import re
import sys
import argparse
import io
from copy import deepcopy
from collections import OrderedDict

from Bio.Alphabet import IUPAC
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

sys.path.insert(0, "./")
import MyFuncs
import AlignBuddy as Alb
import SeqBuddy as Sb
import buddy_resources as br

TEMP_DIR = MyFuncs.TempDir()
VERSION = Sb.VERSION
BACKUP_PATH = os.environ["PATH"]


def fmt(prog):
    return br.CustomHelpFormatter(prog)

parser = argparse.ArgumentParser(prog="alignBuddy", formatter_class=fmt, add_help=False, usage=argparse.SUPPRESS,
                                     description='''\
\033[1mAlignBuddy\033[m
  Sequence alignments with a splash of kava.

\033[1mUsage examples\033[m:
  AlignBuddy.py "/path/to/align_file" -<cmd>
  AlignBuddy.py "/path/to/align_file" -<cmd> | AlignBuddy.py -<cmd>
  AlignBuddy.py "/path/to/seq_file" -ga "mafft" -p "--auto --thread 8"
''')

br.flags(parser, ("alignments", "The file(s) you want to start working on"),
         br.alb_flags, br.alb_modifiers, VERSION)

# This is to allow py.test to work with the -x flag
parser.add_argument("-x", nargs="?")
parser.add_argument("--cov", nargs="?")
parser.add_argument("--cov-report", nargs="?")
in_args = parser.parse_args()


def align_to_hash(_alignbuddy, mode='hash'):
    if mode != "hash":
        return str(_alignbuddy)
    _hash = md5("{0}\n".format(str(_alignbuddy).rstrip()).encode()).hexdigest()
    return _hash

root_dir = os.getcwd()


def string2hash(_input):
    return md5(_input.encode()).hexdigest()


def resource(file_name):
    return "{0}/unit_test_resources/{1}".format(root_dir, file_name)


# ################### Alignment resources ################### #
'''
# Deprecated --> Delete when possible
align_files = ["Mnemiopsis_cds.nex", "Mnemiopsis_cds.phy", "Mnemiopsis_cds.phyr", "Mnemiopsis_cds.stklm",
               "Mnemiopsis_pep.nex", "Mnemiopsis_pep.phy", "Mnemiopsis_pep.phyr", "Mnemiopsis_pep.stklm",
               "Alignments_pep.phy", "Alignments_pep.phyr", "Alignments_pep.stklm",
               "Alignments_cds.phyr", "Alignments_cds.stklm"]

file_types = ["nexus", "phylip-relaxed", "phylip-relaxed", "stockholm",
              "nexus", "phylip-relaxed", "phylip-relaxed", "stockholm",
              "phylip-relaxed", "phylip-relaxed", "stockholm",
              "phylip-relaxed", "stockholm"]

nucl_indices = [0, 1, 2, 3, 11, 12]

input_tuples = [(next_file, file_types[indx]) for indx, next_file in enumerate(align_files)]
alb_objects = [Alb.AlignBuddy(resource(x)) for x in align_files]
'''


class Resources:
    def __init__(self):
        one_dna = OrderedDict([("clustal", "Mnemiopsis_cds.clus"),
                               ("fasta", "Mnemiopsis_cds_aln.fa"),
                               ("gb", "Mnemiopsis_cds_aln.gb"),
                               ("nexus", "Mnemiopsis_cds.nex"),
                               ("phylip", "Mnemiopsis_cds.phy"),
                               ("phylipr", "Mnemiopsis_cds.phyr"),
                               ("phylipss", "Mnemiopsis_cds.physs"),
                               ("phylipsr", "Mnemiopsis_cds.physr"),
                               ("stockholm", "Mnemiopsis_cds.stklm")])
        one_rna = OrderedDict([("nexus", "Mnemiopsis_rna.nex")])
        one_pep = OrderedDict([("gb", "Mnemiopsis_pep_aln.gb"),
                               ("nexus", "Mnemiopsis_pep.nex"),
                               ("phylip", "Mnemiopsis_pep.phy"),
                               ("phylipr", "Mnemiopsis_pep.phyr"),
                               ("phylipss", "Mnemiopsis_pep.physs"),
                               ("phylipsr", "Mnemiopsis_pep.physr"),
                               ("stockholm", "Mnemiopsis_pep.stklm")])

        one_aligns = OrderedDict([("dna", one_dna),
                                  ("rna", one_rna),
                                  ("pep", one_pep)])

        multi_dna = OrderedDict([("clustal", "Alignments_cds.clus"),
                                 ("phylip", "Alignments_cds.phy"),
                                 ("phylipr", "Alignments_cds.phyr"),
                                 ("phylipss", "Alignments_cds.physs"),
                                 ("phylipsr", "Alignments_cds.physr"),
                                 ("stockholm", "Alignments_cds.stklm")])
        multi_pep = OrderedDict([("clustal", "Alignments_pep.clus"),
                                 ("phylip", "Alignments_pep.phy"),
                                 ("phylipr", "Alignments_pep.phyr"),
                                 ("phylipss", "Alignments_pep.physs"),
                                 ("phylipsr", "Alignments_pep.physr"),
                                 ("stockholm", "Alignments_pep.stklm")])

        multi_aligns = OrderedDict([("dna", multi_dna),
                                    ("pep", multi_pep)])

        self.resources = OrderedDict([("one", one_aligns), ("multi", multi_aligns)])

        self.alb_objs = OrderedDict()
        self.res_paths = OrderedDict()
        for num in self.resources:
            self.alb_objs.setdefault(num, OrderedDict())
            self.res_paths.setdefault(num, OrderedDict())
            for _type in self.resources[num]:
                self.res_paths[num][_type] = OrderedDict([(key, resource(path))
                                                         for key, path in self.resources[num][_type].items()])

                self.alb_objs[num][_type] = OrderedDict([(key, Alb.AlignBuddy(resource(path)))
                                                         for key, path in self.resources[num][_type].items()])

        self.code_dict = OrderedDict([("num_aligns", OrderedDict([("o", "one"), ("m", "multi")])),
                                      ("type", OrderedDict([("p", "pep"), ("d", "dna"), ("r", "rna")])),
                                      ("format", OrderedDict([("c", "clustal"), ("f", "fasta"), ("g", "gb"),
                                                              ("n", "nexus"), ("py", "phylip"), ("pr", "phylipr"),
                                                              ("pss", "phylipss"), ("psr", "phylipsr"),
                                                              ("s", "stockholm")]))])

    def _parse_code(self, code=""):
        results = OrderedDict([("num_aligns", []), ("type", []), ("format", [])])
        code = code.split()
        for i in code:
            for j in results:
                if i in self.code_dict[j]:
                    results[j].append(i)

        # Fill up a field with all possibilities if nothing is given
        results["num_aligns"] = [key for key in self.code_dict["num_aligns"]] \
            if not results["num_aligns"] else results["num_aligns"]
        results["type"] = [key for key in self.code_dict["type"]] if not results["type"] else results["type"]
        results["format"] = [key for key in self.code_dict["format"]] if not results["format"] else results["format"]
        return results

    def get(self, code="", mode="objs"):
        """
        Returns copies of AlignBuddy objects, the
        :param code:
        :param mode: {"objs", "paths"}
        :return: OrderedDict {key: resource}
        """
        files = self._parse_code(code)
        output = OrderedDict()
        key = ["", "", ""]
        for num_aligns in files["num_aligns"]:
            key[0] = num_aligns
            n = self.code_dict["num_aligns"][num_aligns]
            for _type in files["type"]:
                key[1] = _type
                t = self.code_dict["type"][_type]
                for _format in files["format"]:
                    key[2] = _format
                    f = self.code_dict["format"][_format]
                    try:
                        assert not " ".join(key) in output
                        if mode == "objs":
                            output[" ".join(key)] = Alb.make_copy(self.alb_objs[n][t][f])
                        elif mode == "paths":
                            output[" ".join(key)] = self.res_paths[n][t][f]
                        else:
                            raise ValueError("The 'mode' parameter only accepts 'objs' or 'paths' as input.")
                    except KeyError:
                        pass
        return output

    def get_list(self, code="", mode="objs"):
        return [value for key, value in self.get(code=code, mode=mode).items()]

    def get_one(self, key, mode="objs"):
        output = self.get_list(key, mode)
        return None if not output or len(output) > 1 else output[0]

    def deets(self, key):
        key = key.split()
        return {"num_aligns": self.code_dict["num_aligns"][key[0]],
                "type": self.code_dict["type"][key[1]],
                "format": br.parse_format(self.code_dict["format"][key[2]])}


alignments = Resources()


@pytest.mark.parametrize("key, align_file", alignments.get(mode="paths").items())
def test_instantiate_alignbuddy_from_file(key, align_file):
    key = key.split()
    print(key)
    assert type(Alb.AlignBuddy(align_file, in_format=alignments.code_dict["format"][key[2]])) == Alb.AlignBuddy


@pytest.mark.parametrize("align_file", alignments.get_list(mode="paths"))
def test_instantiate_alignbuddy_from_file_guess(align_file):
    assert type(Alb.AlignBuddy(align_file)) == Alb.AlignBuddy


@pytest.mark.parametrize("align_file", alignments.get_list(mode="paths"))
def test_instantiate_alignbuddy_from_handle(align_file):
    with open(align_file, 'r') as ifile:
        assert type(Alb.AlignBuddy(ifile)) == Alb.AlignBuddy


@pytest.mark.parametrize("align_file", alignments.get_list(mode="paths"))
def test_instantiate_alignbuddy_from_raw(align_file):
    with open(align_file, 'r') as ifile:
        assert type(Alb.AlignBuddy(ifile.read())) == Alb.AlignBuddy


@pytest.mark.parametrize("alignbuddy", alignments.get_list(mode="objs"))
def test_instantiate_alignbuddy_from_alignbuddy(alignbuddy):
    assert type(Alb.AlignBuddy(alignbuddy)) == Alb.AlignBuddy


@pytest.mark.parametrize("alignbuddy", alignments.get_list(mode="objs"))
def test_instantiate_alignbuddy_from_list(alignbuddy):
    assert type(Alb.AlignBuddy(alignbuddy.alignments)) == Alb.AlignBuddy

    with pytest.raises(TypeError):  # When non-MultipleSeqAlignment objects are in the .alignments list
        alignbuddy.alignments.append("Dummy string object")
        Alb.AlignBuddy(alignbuddy.alignments)


def test_instantiation_alignbuddy_errors():
    with pytest.raises(br.GuessError) as e:
        Alb.AlignBuddy(resource("gibberish.fa"))
    assert "Could not determine format from _input file" in str(e)

    tester = open(resource("gibberish.fa"), "r")
    with pytest.raises(br.GuessError) as e:
        Alb.AlignBuddy(tester.read())
    assert "Could not determine format from raw" in str(e)

    tester.seek(0)
    with pytest.raises(br.GuessError) as e:
        Alb.AlignBuddy(tester)
    assert "Could not determine format from input file-like object" in str(e)


def test_empty_file():
    with open(resource("blank.fa"), "r") as ifile:
        with pytest.raises(br.GuessError) as e:
            Alb.AlignBuddy(ifile)
        assert "Empty file" in str(e)


# ##################### AlignBuddy methods ###################### ##
def test_set_format():
    tester = alignments.get_list("o d g")[0]
    tester.set_format("fasta")
    assert tester._out_format == "fasta"


def test_records():
    tester = alignments.get_list("m p py")[0]
    assert len(tester.records()) == 29


def test_records_iter():
    tester = alignments.get_list("m p py")[0]
    counter = 0
    for rec in tester.records_iter():
        assert type(rec) == SeqRecord
        counter += 1
    assert counter == 29


hashes = {'o p g': 'bf8485cbd30ff8986c2f50b677da4332', 'o p n': '17ff1b919cac899c5f918ce8d71904f6',
          'o p py': '968ed9fa772e65750f201000d7da670f', 'o p pr': 'ce423d5b99d5917fbef6f3b47df40513',
          "o p pss": "4bd927145de635c429b2917e0a1db176", "o p psr": "8ff80c7f0b8fc7f237060f94603c17be",
          'o p s': 'c0dce60745515b31a27de1f919083fe9',

          'o d c': '778874422d0baadadcdfce81a2a81229', 'o d f': '98a3a08389284461ea9379c217e99770',
          'o d g': '2a42c56df314609d042bdbfa742871a3', 'o d n': 'cb1169c2dd357771a97a02ae2160935d',
          'o d py': '503e23720beea201f8fadf5dabda75e4', 'o d pr': '52c23bd793c9761b7c0f897d3d757c12',
          'o d pss': '4c0c1c0c63298786e6fb3db1385af4d5', 'o d psr': 'c5fb6a5ce437afa1a4004e4f8780ad68',
          'o d s': '228e36a30e8433e4ee2cd78c3290fa6b',

          'o r n': 'f3bd73151645359af5db50d2bdb6a33d',

          'm p c': '1a043fcd3e0a2194102dfbf500cb267f', 'm p s': '3fd5805f61777f7f329767c5f0fb7467',
          'm p py': '2a77f5761d4f51b88cb86b079e564e3b', 'm p pr': '3fef9a05058a5259ebd517d1500388d4',
          'm p pss': 'eb82cda31fcb2cf00e11d7e910fde695', 'm p psr': 'a16c6e617e5a88fef080eea54e54e8a8',

          'm d c': '5eacb9bf16780aeb5d031d10dc9bab6f', 'm d s': 'ae352b908be94738d6d9cd54770e5b5d',
          'm d py': '42679a32ebd93b628303865f68b0293d', 'm d pr': '22c0f0c8f014a34be8edd394bf477a2d',
          'm d pss': 'c789860da8f0b59e0adc7bde6342b4b0', 'm d psr': '28b2861275e0a488042cff35393ac36d'}

albs = [(hashes[key], alignbuddy) for key, alignbuddy in alignments.get("").items()]


@pytest.mark.parametrize("next_hash,alignbuddy", albs)
def test_print(next_hash, alignbuddy, capsys):
    alignbuddy.print()
    out, err = capsys.readouterr()
    out = "{0}\n".format(out.rstrip())
    tester = string2hash(out)
    assert tester == next_hash


@pytest.mark.parametrize("next_hash,alignbuddy", albs)
def test_str(next_hash, alignbuddy):
    tester = str(alignbuddy)
    tester = string2hash(tester)
    assert tester == next_hash


@pytest.mark.parametrize("next_hash,alignbuddy", albs)
def test_write1(next_hash, alignbuddy):
    temp_file = MyFuncs.TempFile()
    alignbuddy.write(temp_file.path)
    out = "{0}\n".format(temp_file.read().rstrip())
    tester = string2hash(out)
    assert tester == next_hash


def test_write2():  # Unloopable components
    tester = alignments.get_one("m p py")
    tester.set_format("fasta")
    with pytest.raises(ValueError):
        str(tester)

    tester.alignments = []
    assert str(tester) == "AlignBuddy object contains no alignments.\n"

    tester = alignments.get_one("o d pr")
    tester.set_format("phylipi")
    assert align_to_hash(tester) == "52c23bd793c9761b7c0f897d3d757c12"

    tester = Alb.AlignBuddy(resource("Mnemiopsis_cds_hashed_ids.nex"))
    tester.set_format("phylip-strict")
    assert align_to_hash(tester) == "16b3397d6315786e8ad8b66e0d9c798f"


# ################################################# HELPER FUNCTIONS ################################################# #
def test_guess_error():
    # File path
    with pytest.raises(br.GuessError):
        Alb.AlignBuddy(resource("unrecognizable.txt"))

    with open(resource("unrecognizable.txt"), 'r') as ifile:
        # Raw
        with pytest.raises(br.GuessError) as e:
            Alb.AlignBuddy(ifile.read())
        assert "Could not determine format from raw input" in str(e)

        # Handle
        with pytest.raises(br.GuessError) as e:
            ifile.seek(0)
            Alb.AlignBuddy(ifile)
        assert "Could not determine format from input file-like object" in str(e)

    # GuessError output
    try:
        Alb.AlignBuddy(resource("unrecognizable.txt"))
    except br.GuessError as e:
        assert "Could not determine format from _input file" in str(e) and \
               "\nTry explicitly setting with -f flag." in str(e)


def test_guess_alphabet():
    for alb in alignments.get_list("d"):
        assert Alb.guess_alphabet(alb) == IUPAC.ambiguous_dna
    for alb in alignments.get_list("p"):
        assert Alb.guess_alphabet(alb) == IUPAC.protein
    for alb in alignments.get_list("r"):
        assert Alb.guess_alphabet(alb) == IUPAC.ambiguous_rna

    assert not Alb.guess_alphabet(Alb.AlignBuddy("", in_format="fasta"))


def test_guess_format():
    assert Alb.guess_format(["dummy", "list"]) == "stockholm"

    for key, obj in alignments.get().items():
        assert Alb.guess_format(obj) == alignments.deets(key)["format"]

    for key, path in alignments.get(mode="paths").items():
        assert Alb.guess_format(path) == alignments.deets(key)["format"]
        with open(path, "r") as ifile:
            assert Alb.guess_format(ifile) == alignments.deets(key)["format"]
            ifile.seek(0)
            string_io = io.StringIO(ifile.read())
        assert Alb.guess_format(string_io) == alignments.deets(key)["format"]

    Alb.guess_format(resource("blank.fa")) == "empty file"
    assert not Alb.guess_format(resource("malformed_phylip_records.physs"))
    assert not Alb.guess_format(resource("malformed_phylip_columns.physs"))

    with pytest.raises(br.GuessError) as e:
        Alb.guess_format({"Dummy dict": "Type not recognized by guess_format()"})
    assert "Unsupported _input argument in guess_format()" in str(e)


def test_parse_format():
    for _format in ["phylip", "phylipis", "phylip-strict", "phylip-interleaved-strict"]:
        assert br.parse_format(_format) == "phylip"

    for _format in ["phylipi", "phylip-relaxed", "phylip-interleaved", "phylipr"]:
        assert br.parse_format(_format) == "phylip-relaxed"

    for _format in ["phylips", "phylipsr", "phylip-sequential", "phylip-sequential-relaxed"]:
        assert br.parse_format(_format) == "phylipsr"

    for _format in ["phylipss", "phylip-sequential-strict"]:
        assert br.parse_format(_format) == "phylipss"

    with pytest.raises(TypeError) as e:
        br.parse_format("foo")
    assert "Format type 'foo' is not recognized/supported" in str(e)


def test_make_copy():
    for alb in alignments.get_list():
        tester = Alb.make_copy(alb)
        align_to_hash(tester) == align_to_hash(alb)


def test_stderr(capsys):
    Alb._stderr("Hello std_err", quiet=False)
    out, err = capsys.readouterr()
    assert err == "Hello std_err"

    Alb._stderr("Hello std_err", quiet=True)
    out, err = capsys.readouterr()
    assert err == ""


def test_stdout(capsys):
    Alb._stdout("Hello std_out", quiet=False)
    out, err = capsys.readouterr()
    assert out == "Hello std_out"

    Alb._stdout("Hello std_out", quiet=True)
    out, err = capsys.readouterr()
    assert out == ""


# ################################################ MAIN API FUNCTIONS ################################################ #
# ##########################################  '-al', '--alignment_lengths' ############################################ #
def test_alignment_lengths():
    lengths = Alb.alignment_lengths(alignments.get_one("m p c"))
    assert lengths[0] == 481
    assert lengths[1] == 683

    lengths = Alb.alignment_lengths(alignments.get_one("m d s"))
    assert lengths[0] == 2043
    assert lengths[1] == 1440


# ##############################################  '-cs', '--clean_seqs' ############################################### #
def test_clean_seqs():
    # Test an amino acid file
    tester = Alb.clean_seq(alignments.get_one("m p py"))
    assert align_to_hash(tester) == "07a861a1c80753e7f89f092602271072"

    tester = Alb.clean_seq(Alb.AlignBuddy(resource("ambiguous_dna_alignment.fa")), ambiguous=False, rep_char="X")
    assert align_to_hash(tester) == "6755ea1408eddd0e5f267349c287d989"


# ###########################################  '-cta', '--concat_alignments' ######################################### #
def test_concat_alignments():
    with pytest.raises(AttributeError) as e:
        Alb.concat_alignments(alignments.get_one("p o g"), '.*')
    assert "Please provide at least two alignments." in str(e)

    tester = alignments.get_one("o p g")
    tester.alignments.append(alignments.get_one("o p g").alignments[0])

    with pytest.raises(ValueError) as e:
        Alb.concat_alignments(tester, 'foo')
    assert "No match found for record" in str(e)

    with pytest.raises(ValueError) as e:
        Alb.concat_alignments(tester, 'Panx')
    assert "Replicate matches" in str(e)

    tester = Sb.SeqBuddy(resource("Cnidaria_pep.nexus"))
    Sb.pull_recs(tester, "Ccr|Cla|Hec")
    tester = Alb.AlignBuddy(str(tester))
    tester.alignments.append(tester.alignments[0])
    assert align_to_hash(Alb.concat_alignments(Alb.make_copy(tester))) == '32a507107b7dcd044ea7760c8812441c'

    tester.set_format("gb")
    assert align_to_hash(Alb.concat_alignments(Alb.make_copy(tester),
                                               "(.).(.)-Panx(.)")) == '5ac908ebf7918a45664a31da480fda58'

    tester.set_format("gb")
    assert align_to_hash(Alb.concat_alignments(Alb.make_copy(tester),
                                               "(.).(.)-Panx(.)")) == '5ac908ebf7918a45664a31da480fda58'

    tester.set_format("gb")
    assert align_to_hash(Alb.concat_alignments(Alb.make_copy(tester),
                                               "...", "Panx.*")) == 'e754350b0397cf54f531421d1e85774f'

    tester.set_format("gb")
    assert align_to_hash(Alb.concat_alignments(Alb.make_copy(tester),
                                               "...", "(P)an(x)(.)")) == '5c6653aec09489cadcbed68fbd2f7465'

    shorten = Alb.delete_records(Alb.make_copy(tester), "Ccr")
    tester.alignments[1] = shorten.alignments[1]
    assert align_to_hash(Alb.concat_alignments(Alb.make_copy(tester))) == 'f3ed9139ab6f97042a244d3f791228b6'

# ###########################################  '-con', '--consensus' ############################################ #
hashes = {'o d g': '888a13e13666afb4d3d851ca9150b442', 'o d n': '560d4fc4be7af5d09eb57a9c78dcbccf',
          'o d py': '01f1181187ffdba4fb08f4011a962642', 'o d s': '51b5cf4bb7d591c9d04c7f6b6bd70692',
          'o r n': '1123b95374085b5bcd079880b7762801', 'o p g': '2c038a306713800301b6b4cdbcf61659',
          'o p n': '756a3334c70f9272e2d9cb74dba9ad52', 'o p py': 'aaf1d5aff561c1769dd267ada2fea8b0',
          'o p s': 'b6f72510eeef6be0752ae86d72a44283', 'm d py': '0ae422fa0fafbe0f2edab9a042fb7834',
          'm d s': '7b0aa3cca159b276158cf98209be7dab', 'm p py': '460033d892db36d4750bafc6998d42d0',
          'm p s': '89130797253646e61b78ab7d91ad3fd9'}

hashes = [(alignbuddy, hashes[key]) for key, alignbuddy in alignments.get("o m d r p g n py s").items()]


@pytest.mark.parametrize("alignbuddy,next_hash", hashes)
def test_consensus(alignbuddy, next_hash):
    tester = Alb.consensus_sequence(alignbuddy)
    assert align_to_hash(tester) == next_hash

# ###########################################  '-dr', '--delete_records' ############################################ #
hashes = {'o d g': '3c7ecdcad18801a86c394de200ef6de9', 'o d n': '355a98dad5cf382797eb907e83940978',
          'o d py': 'fe9a2776558f3fe9a1732c777c4bc9ac', 'o d s': '35dc92c4f4697fb508eb1feca43d9d75',
          'o r n': '96e6964115200d46c7cb4eb975718304', 'o p g': 'f5e2184a88d3663528e011af80e2f6c0',
          'o p n': '1cfaa4109c5db8fbfeaedabdc57af655', 'o p py': '1d0e7b4d8e89b42b0ef7cc8c40ed1a93',
          'o p s': '1578d98739d2aa6196463957c7b408fa', 'm d py': 'db4ed247b40707e8e1f0622bb420733b',
          'm d s': 'de5beddbc7f0a7f8e3dc2d5fd43b7b29', 'm p py': '31f91f7dc548e4b075bfb0fdd7d5c82c',
          'm p s': '043e35023b355ed560166db9130cfe30'}

hashes = [(alignbuddy, hashes[key]) for key, alignbuddy in alignments.get("o m d r p g n py s").items()]


@pytest.mark.parametrize("alignbuddy,next_hash", hashes)
def test_delete_records(alignbuddy, next_hash):
    tester = Alb.delete_records(alignbuddy, "α[1-5]|β[A-M]")
    assert align_to_hash(tester) == next_hash

# ######################  'd2r', '--transcribe' and 'r2d', '--back_transcribe' ###################### #
d2r_hashes = {'o d g': '4bf291d91d4b27923ef07c660b011c72', 'o d n': 'e531dc31f24192f90aa1f4b6195185b0',
              'o d py': 'e55bd18b6d82a7fc3150338173e57e6a', 'o d s': '45b511f34653e3b984e412182edee3ca',
              'm d py': '16cb082f5cd9f103292ccea0c4d65a06', 'm d s': 'd81dae9714a553bddbf38084f7a8e00e'}

r2d_hashes = {'o d g': '2a42c56df314609d042bdbfa742871a3', 'o d n': 'cb1169c2dd357771a97a02ae2160935d',
              'o d py': '503e23720beea201f8fadf5dabda75e4', 'o d s': '228e36a30e8433e4ee2cd78c3290fa6b',
              'm d py': '42679a32ebd93b628303865f68b0293d', 'm d s': 'ae352b908be94738d6d9cd54770e5b5d'}

hashes = [(alignbuddy, d2r_hashes[key], r2d_hashes[key]) for key, alignbuddy in alignments.get("o m d g py s").items()]


@pytest.mark.parametrize("alignbuddy,d2r_hash,r2d_hash", hashes)
def test_transcribe(alignbuddy, d2r_hash, r2d_hash):
    tester = Alb.dna2rna(alignbuddy)
    assert align_to_hash(tester) == d2r_hash
    tester = Alb.rna2dna(tester)
    assert align_to_hash(tester) == r2d_hash


def test_transcribe_exceptions():
    with pytest.raises(TypeError) as e:
        Alb.dna2rna(alignments.get_one("o p s"))
    assert "TypeError: DNA sequence required, not IUPACProtein()." in str(e)

    with pytest.raises(TypeError) as e:
        Alb.dna2rna(alignments.get_one("o r n"))
    assert "TypeError: DNA sequence required, not IUPACAmbiguousRNA()." in str(e)


def test_back_transcribe_exceptions():  # Asserts that a TypeError will be thrown if user inputs protein
    with pytest.raises(TypeError) as e:
        Alb.rna2dna(alignments.get_one("o p s"))
    assert "TypeError: RNA sequence required, not IUPACProtein()." in str(e)

    with pytest.raises(TypeError) as e:
        Alb.rna2dna(alignments.get_one("o d s"))
    assert "TypeError: RNA sequence required, not IUPACAmbiguousDNA()." in str(e)

# ###########################################  '-et', '--enforce_triplets' ############################################ #
hashes = {'o d g': '4fabe926e9d66c40b5833cda32506f4a', 'o d n': 'c907d29434fe2b45db60f1a9b70f110d',
          'o d py': 'b6cf61c86588023b58257c9008c862b5', 'o r n': '0ed7383ab2897f8350c2791739f0b0a4',
          "m d py": "669ffc4fa602fb101c559cb576bddee1"}
hashes = [(alignbuddy, hashes[key]) for key, alignbuddy in alignments.get("m o d r g n py").items()]


@pytest.mark.parametrize("alignbuddy,next_hash", hashes)
def test_enforce_triplets(alignbuddy, next_hash):
    tester = Alb.enforce_triplets(alignbuddy)
    assert align_to_hash(tester) == next_hash


def test_enforce_triplets_error():
    with pytest.raises(TypeError) as e:
        Alb.enforce_triplets(alignments.get_one("m p c"))
    assert "Nucleic acid sequence required, not protein." in str(e)

    with pytest.raises(TypeError) as e:
        tester = Alb.enforce_triplets(alignments.get_one("m d pr"))
        tester.alignments[0][0].seq = Seq("MLDILSKFKGVTPFKGITIDDGWDQLNRSFMFVLLVVMGTTVTVRQYTGSVISCDGFKKFGSTFAEDYCWTQGLY",
                                          alphabet=IUPAC.protein)
        Alb.enforce_triplets(tester)
    assert "Record 'Mle-Panxα9' is protein. Nucleic acid sequence required." in str(e)

# ###########################################  'er', '--extract_range' ############################################ #
hashes = {'o d g': 'e90851d2b94c07f6ff5be35c4bacb683', 'o d n': '10ca718b74f3b137c083a766cb737f31',
          'o d py': 'd738a9ab3ab200a7e013177e1042e86c', 'o p g': 'b094576bb8a5eadbc936235719530c6f',
          'o p n': '5f400edc6f0990c0cd6eb52ae7687e39', 'o p py': '69c9ad73ae02525150d4682f9dd68093',
          "m d py": "d06ba679c8a686c8f077bb460a4193b0", "m p py": "8151eeda36b9a170512709829d70230b"}
hashes = [(alignbuddy, hashes[key]) for key, alignbuddy in alignments.get("m o d p g n py").items()]


@pytest.mark.parametrize("alignbuddy,next_hash", hashes)
def test_extract_range(alignbuddy, next_hash):
    tester = Alb.extract_range(alignbuddy, 0, 50)
    assert align_to_hash(tester) == next_hash


# #################################### 'lc', '--lowercase' and 'uc', '--uppercase' ################################### #
uc_hashes = {'o d g': '2a42c56df314609d042bdbfa742871a3', 'o d n': '52e74a09c305d031fc5263d1751e265d',
             'o d py': 'cfe6cb9c80aebd353cf0378a6d284239', 'o d s': 'b82538a4630810c004dc8a4c2d5165ce',
             'o p g': 'bf8485cbd30ff8986c2f50b677da4332', 'o p n': '8b6737fe33058121fd99d2deee2f9a76',
             'o p py': '968ed9fa772e65750f201000d7da670f', 'o p s': 'f35cbc6e929c51481e4ec31e95671638',
             'm d py': '6259e675def07bd4977f4ab1f5ffc26d', 'm d s': 'f3f7b66ef034d3807683a2d5a0c44cad',
             'm p py': '2a77f5761d4f51b88cb86b079e564e3b', 'm p s': '6f3f234d796520c521cb85c66a3e239a'}

lc_hashes = {'o d g': '2a42c56df314609d042bdbfa742871a3', 'o d n': 'cb1169c2dd357771a97a02ae2160935d',
             'o d py': '503e23720beea201f8fadf5dabda75e4', 'o d s': '228e36a30e8433e4ee2cd78c3290fa6b',
             'o p g': 'bf8485cbd30ff8986c2f50b677da4332', 'o p n': '17ff1b919cac899c5f918ce8d71904f6',
             'o p py': 'aacda2f5d4077f23926400f74afa2f46', 'o p s': 'c0dce60745515b31a27de1f919083fe9',
             'm d py': '0974ac9aefb2fb540957f15c4869c242', 'm d s': 'a217b9f6000f9eeff98faeb9fd09efe4',
             'm p py': 'd13551548c9c1e966d0519755a8fb4eb', 'm p s': '00661f7afb419c6bb8c9ac654af7c976'}

hashes = [(alignbuddy, uc_hashes[key], lc_hashes[key],) for key, alignbuddy in alignments.get("o m d p g py s").items()]


@pytest.mark.parametrize("alignbuddy,uc_hash,lc_hash", hashes)
def test_cases(alignbuddy, uc_hash, lc_hash):
    tester = Alb.uppercase(alignbuddy)
    assert align_to_hash(tester) == uc_hash
    tester = Alb.lowercase(tester)
    assert align_to_hash(tester) == lc_hash


# ##################### '-mf2a', '--map_features2alignment' ###################### ##
hashes = {"o p n": "06befa060809bfcc8d4ceba16b2942e8", "o p pr": "57906e7e85db021f79366d95f64aef41",
          "o p psr": "57906e7e85db021f79366d95f64aef41", "o p s": "21850752df36bafeabc6141f5f277071",
          "o d n": "2d8b6524010177f6507dde387146378c", "o d pr": "eec68b8696f09d199e8a6b75e50ec18a",
          "o d psr": "eec68b8696f09d199e8a6b75e50ec18a", "o d s": "3b0fb43a76bb5057cc1bd001b36b9374"}
hashes = [(alignbuddy, hashes[key]) for key, alignbuddy in alignments.get("o p d n pr psr s").items()]


@pytest.mark.parametrize("alignbuddy,next_hash", hashes)
def test_map_features2alignment(alignbuddy, next_hash):
    if alignbuddy.alpha == IUPAC.protein:
        seqbuddy = Sb.SeqBuddy(resource("Mnemiopsis_pep.gb"))
    else:
        seqbuddy = Sb.SeqBuddy(resource("Mnemiopsis_cds.gb"))
    tester = Alb.map_features2alignment(seqbuddy, alignbuddy)
    tester.set_format("genbank")
    assert align_to_hash(tester) == next_hash


# ###########################################  '-oi', '--order_ids' ############################################ #
fwd_hashes = {'o d g': 'acf68c9196faa0960007abc40ba87244', 'o d n': '60bbc6306cbb4eb903b1212718bb4592',
              'o d py': '3c49bdc1b0fe4e1d6bfc148eb0293e21', 'o p g': '7fb69602ffac95a5eecd106876640fcc',
              'o p n': '9a790b9525ca8b1ac3cae3b98ca24b30', 'o p py': 'ffae954adc0d362354e43c1b70d9be29',
              'm d py': 'a44938e26e4b35967ed8e17a0eaebe4c', 'm p py': '5bdda310b29b18057e056f3c982446b2'}

rev_hashes = {'o d g': 'a593a2cd979f52c356c61e10ca9a1317', 'o d n': '82fea6e3d3615ac75ec5022abce255da',
              'o d py': 'd6e79a5faeaff396aa7eab0b460c3eb9', 'o p g': '39af830e6d3605ea1dd04979a4a33f54',
              'o p n': '85b3562b0eb0246d7dab56a4bcc6e2ae', 'o p py': 'f4c0924087fdb624823d02e909d94e95',
              'm d py': '9d6b6087d07f7d1fd701591ab7cb576d', 'm p py': '439f57b891dd2a72724b10c124f96378'}
hashes = [(alignbuddy, fwd_hashes[key], rev_hashes[key]) for key, alignbuddy in alignments.get("m o d p g n py").items()]


@pytest.mark.parametrize("alignbuddy,fwd_hash,rev_hash", hashes)
def test_order_ids(alignbuddy, fwd_hash, rev_hash):
    Alb.order_ids(alignbuddy)
    assert align_to_hash(alignbuddy) == fwd_hash

    Alb.order_ids(alignbuddy, reverse=True)
    assert align_to_hash(alignbuddy) == rev_hash


# ##################### '-pr', '--pull_records' ###################### ##
hashes = {'o d g': '04572f1d4e58b678459692ef2747979f', 'o d n': 'd82e66c57548bcf8cba202b13b070ead',
          'o d py': 'd141752c38a892ccca800c637f609608', 'o p g': '5782b8de656ceb793a19e6d6e059f8df',
          'o p n': '027bbc7e34522f9521f83ee7d03793a1', 'o p py': '2cd74d7ede4d1fb6e18363567426437e',
          'm d py': '7c77c6f3245c21842f4be585714ec6ce', 'm p py': 'f34fa4c34cfe5c1e6b228949557c9483'}

hashes = [(alignbuddy, hashes[key]) for key, alignbuddy in alignments.get("m o d p g n py").items()]


@pytest.mark.parametrize("alignbuddy,next_hash", hashes)
def test_pull_records(alignbuddy, next_hash):
    Alb.pull_records(alignbuddy, "α[1-5]$|β[A-M]")
    assert align_to_hash(alignbuddy) == next_hash

'''
# ###########################################  'd2r', '--transcribe' ############################################ #
d2r_hashes = ['e531dc31f24192f90aa1f4b6195185b0', 'b34e4d1dcf0a3a36d36f2be630934d29',
              'a083e03b4e0242fa3c23afa80424d670', '45b511f34653e3b984e412182edee3ca']
d2r_hashes = [(Alb.make_copy(alb_objects[x]), value) for x, value in enumerate(d2r_hashes)]


@pytest.mark.parametrize("alignbuddy, next_hash", d2r_hashes)
def test_transcribe(alignbuddy, next_hash):
    assert align_to_hash(Alb.dna2rna(alignbuddy)) == next_hash


def test_transcribe_pep_exception():
    with pytest.raises(ValueError):
        Alb.dna2rna(deepcopy(alb_objects[4]))


# ###########################################  'ga', '--generate_alignment' ########################################## #
# This is tested for PAGAN version 0.61
@pytest.mark.generate_alignments
def test_pagan_inputs():
    # FASTA
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'pagan')
    assert align_to_hash(tester) == 'da1c6bb365e2da8cb4e7fad32d7dafdb'


@pytest.mark.generate_alignments
def test_pagan_outputs():
    # NEXUS
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'pagan', '-f nexus')
    assert align_to_hash(tester) == 'f93607e234441a2577fa7d8a387ef7ec'
    # PHYLIPI
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'pagan', '-f phylipi')
    assert align_to_hash(tester) == '09dd492fde598670d7cfee61d4e2eab8'
    # PHYLIPS
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'pagan', '-f phylips')
    assert align_to_hash(tester) == 'f079eddd44ffbe038e1418ab03ff7e64'


@pytest.mark.generate_alignments
def test_pagan_multi_param():
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'pagan', '-f nexus --translate')
    assert align_to_hash(tester) == 'dd140ec4eb895ce75d574498a58aa28a'


# PRANK is not deterministic, so just test that something reasonable is returned
@pytest.mark.generate_alignments
def test_prank_inputs():
    # FASTA
    tester = Sb.pull_recs(Sb.SeqBuddy(resource("Mnemiopsis_cds.fa")), 'α1')
    tester = Alb.generate_msa(tester, 'prank', '-once')
    assert tester.out_format == 'fasta'


@pytest.mark.generate_alignments
def test_prank_outputs():
    # NEXUS
    tester = Sb.pull_recs(Sb.SeqBuddy(resource("Mnemiopsis_cds.fa")), 'α1')
    tester = Alb.generate_msa(tester, 'prank', '-f=nexus -once')
    assert tester.out_format == 'nexus'
    # PHYLIPI
    tester = Sb.pull_recs(Sb.SeqBuddy(resource("Mnemiopsis_cds.fa")), 'α1')
    tester = Alb.generate_msa(tester, 'prank', '-f=phylipi -once')
    assert tester.out_format == 'phylip-relaxed'
    # PHYLIPS
    tester = Sb.pull_recs(Sb.SeqBuddy(resource("Mnemiopsis_cds.fa")), 'α1')
    tester = Alb.generate_msa(tester, 'prank', '-f=phylips -once')
    assert tester.out_format == 'phylip-sequential'


@pytest.mark.generate_alignments
def test_muscle_inputs():
    # FASTA
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'muscle')
    assert align_to_hash(tester) == '60ada1630165a40be9d5700cc228b1e1'


@pytest.mark.generate_alignments
def test_muscle_outputs():
    # FASTA
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'muscle', '-clw')
    assert align_to_hash(tester) == 'ff8d81f75dfd6249ba1e91e5bbc8bdce'


@pytest.mark.generate_alignments
def test_muscle_multi_param():
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'muscle', '-clw -diags')
    assert align_to_hash(tester) == 'ff8d81f75dfd6249ba1e91e5bbc8bdce'


@pytest.mark.generate_alignments
def test_clustalw2_inputs():
    # FASTA
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalw2')
    assert align_to_hash(tester) == 'd744b9cadf592a6d4e8d5eefef90e7c7'


@pytest.mark.generate_alignments
def test_clustalw2_outputs():
    # NEXUS
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalw2', '-output=nexus')
    assert align_to_hash(tester) == 'f4a61a8c2d08a1d84a736231a4035e2e'
    # PHYLIP
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalw2', '-output=phylip')
    assert align_to_hash(tester) == 'a9490f124039c6a2a6193d27d3d01205'
    # FASTA
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalw2', '-output=fasta')
    assert align_to_hash(tester) == '955440b5139c8e6d7d3843b7acab8446'


@pytest.mark.generate_alignments
def test_clustalw2_multi_param():
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalw2', '-output=phylip -noweights')
    assert align_to_hash(tester) == 'ae9126eb8c482a82d4060d175803c478'


@pytest.mark.generate_alignments
def test_clustalomega_inputs():
    # FASTA
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalomega')
    assert align_to_hash(tester) == 'c041c78d3d3a62a027490a139ad435e4'
    # PHYLIP
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.phy"))
    tester = Alb.generate_msa(tester, 'clustalomega')
    assert align_to_hash(tester) == '734e93bac16fd2fe49a3340086bde048'
    # STOCKHOLM
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.stklm"))
    tester = Alb.generate_msa(tester, 'clustalomega')
    assert align_to_hash(tester) == '5c7a21e173f8bf54a26ed9d49764bf80'


@pytest.mark.generate_alignments
def test_clustalomega_outputs():
    # CLUSTAL
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalomega', '--outfmt=clustal')
    assert align_to_hash(tester) == 'ce25de1a84cc7bfbcd946c88b65cf3e8'
    # PHYLIP
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalomega', '--outfmt=phylip')
    assert align_to_hash(tester) == '692c6af848bd90966f15908903894dbd'
    # STOCKHOLM
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalomega', '--outfmt=stockholm')
    assert align_to_hash(tester) == '47cc879b68719b8de0eb031d2f0e9fcc'


@pytest.mark.generate_alignments
def test_clustalomega_multi_param():
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'clustalomega', '--outfmt=clustal --iter=1')
    assert align_to_hash(tester) == '294d8c0260eb81d2039ce8be7289dfcc'


@pytest.mark.generate_alignments
def test_mafft_inputs():
    # FASTA
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'mafft')
    assert align_to_hash(tester) == '8dda0524aaffb326aff09143a1df8a45'


@pytest.mark.generate_alignments
def test_mafft_outputs():
    # CLUSTAL
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'mafft', '--clustalout')
    assert align_to_hash(tester) == '2b8bf89e7459fe9d0b1f29628df6307e'


@pytest.mark.generate_alignments
def test_mafft_multi_param():
    tester = Sb.SeqBuddy(resource("Mnemiopsis_cds.fa"))
    tester = Alb.generate_msa(tester, 'mafft', '--clustalout --noscore')
    assert align_to_hash(tester) == '2b8bf89e7459fe9d0b1f29628df6307e'


# ###########################################  'ri', '--rename_ids' ############################################ #
def test_rename_ids_several():
    tester = Alb.AlignBuddy(resource("concat_alignment_file.phyr"))
    Alb.rename(tester, 'Mle', 'Xle')
    assert align_to_hash(tester) == '61d03559088c5bdd0fdebd7a8a2061fd'


def test_rename_ids_all_same():
    tester = Alb.make_copy(alb_objects[0])
    Alb.rename(tester, 'Mle', 'Xle')
    assert align_to_hash(tester) == '5a0c20a41fea9054f5476e6fad7c81f6'



# ###########################################  'stf', '--split_alignbuddy' ########################################### #
def test_split_alignment():
    tester = Alb.AlignBuddy(resource("concat_alignment_file.phyr"))
    output = Alb.split_alignbuddy(tester)
    for buddy in output:
        assert buddy.alignments[0] in tester.alignments

# ###########################################  'tr', '--translate' ############################################ #
hashes = ["fa915eafb9eb0bfa0ed8563f0fdf0ef9", "5064c1d6ae6192a829972b7ec0f129ed", "ce423d5b99d5917fbef6f3b47df40513",
          "2340addad40e714268d2523cdb17a78c", "6c66f5f63c5fb98f5855fb1c847486ad", "d9527fe1dfd2ea639df267bb8ee836f7"]
hashes = [(Alb.make_copy(alb_objects[nucl_indices[indx]]), next_hash) for indx, next_hash in enumerate(hashes)]


@pytest.mark.parametrize("alignbuddy,next_hash", hashes)
def test_translate1(alignbuddy, next_hash, capsys):
    tester = Alb.translate_cds(alignbuddy)
    assert align_to_hash(tester) == next_hash

    if next_hash == "6c66f5f63c5fb98f5855fb1c847486ad":
        out, err = capsys.readouterr()
        assert err == "Warning: First codon 'GGT' is not a start codon in Ael_PanxβQ___CDS\n"


def test_translate2():
    # Protein input
    with pytest.raises(TypeError):
        Alb.translate_cds(alb_objects[4])

    # Non-standard length
    tester = Alb.make_copy(alb_objects[0])
    tester.alignments[0][0].seq = Seq(re.sub("-$", "t", str(tester.alignments[0][0].seq)),
                                      alphabet=tester.alignments[0][0].seq.alphabet)
    Alb.translate_cds(tester)
    assert align_to_hash(tester) == "fa915eafb9eb0bfa0ed8563f0fdf0ef9"

    # Final codon not stop and stop codon not at end of seq
    tester = Alb.make_copy(alb_objects[0])
    tester.alignments[0][0].seq = Seq(re.sub("---$", "ttt", str(tester.alignments[0][0].seq)),
                                      alphabet=tester.alignments[0][0].seq.alphabet)
    Alb.translate_cds(tester)
    assert align_to_hash(tester) == "2ca5b0bac98226ee6a53e17503f12197"

    # Non-standard codon
    tester = Alb.AlignBuddy(resource("ambiguous_dna_alignment.fa"))
    Alb.translate_cds(tester)
    assert align_to_hash(tester) == "ab8fb45a38a6e5d553a29f3613bbc1a1"


# ###########################################  'tm', '--trimal' ############################################ #
hashes = ['063e7f52f7c7f19da3a624730cd725a5', '0e2c65d9fc8d4b31cc352b3894837dc1', '4c08805a44e9a0cef08abc53c80f6b4c',
          '9478e5441b88680470f3a4a4db537467', "b1bd83debd405431f290e2e2306a206e", '049b7f9170505ea0799004d964ef33fb',
          '97ea3e55425894d3fe4b817deab003c3', '1f2a937d2c3b020121000822e62c4b96', '4690f58abd6d7f4f3c0d610ea25461c8',
          'b8e65b0a00f55286d57aa76ccfcf04ab', '49a17364aa4bd086c7c432de7baabd07', '82aaad11c9496d8f7e959dd5ce06df4d',
          '4e709de80531c358197f6e1f626c9c58']
hashes = [(Alb.make_copy(alb_objects[x]), value) for x, value in enumerate(hashes)]


@pytest.mark.parametrize("alignbuddy,next_hash", hashes)
def test_trimal(alignbuddy, next_hash):
    Alb.trimal(alignbuddy, .7)
    assert align_to_hash(alignbuddy) == next_hash


def test_trimal2():
    tester = Alb.make_copy(alb_objects[8])
    assert align_to_hash(Alb.trimal(tester, 'clean')) == "a94edb2636a7c9cf177993549371b3e6"
    assert align_to_hash(Alb.trimal(tester, 'gappyout')) == "2ac19a0eecb9901211c1c98a7a203cc2"
    assert align_to_hash(Alb.trimal(tester, 'all')) == "caebb7ace4940cea1b87667e5e113acb"
    with pytest.raises(ValueError):
        Alb.trimal(tester, "Foo")
'''


# ################################################# COMMAND LINE UI ################################################## #
# ##################### '-al', '--alignment_lengths' ###################### ##
def test_alignment_lengths_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.alignment_lengths = True
    Alb.command_line_ui(test_in_args, alignments.get_one("m p c"), skip_exit=True)
    out, err = capsys.readouterr()
    assert out == "481\n683\n"
    assert err == "# Alignment 1\n# Alignment 2\n"

    Alb.command_line_ui(test_in_args, alignments.get_one("o p py"), skip_exit=True)
    out, err = capsys.readouterr()
    assert out == "681\n"
    assert err == ""


# ##################### '-r2d', '--back_transcribe' ###################### ##
def test_back_transcribe_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.back_transcribe = True
    Alb.command_line_ui(test_in_args, alignments.get_one("o r n"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "f8c2b216fa65fef9c74c1d0c4abc2ada"

    with pytest.raises(SystemExit):
        Alb.command_line_ui(test_in_args, alignments.get_one("m d s"))
    out, err = capsys.readouterr()
    assert err == "TypeError: RNA sequence required, not IUPACAmbiguousDNA().\n"


# ##################### '-cs', '--clean_seqs' ###################### ##
def test_clean_seqs_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.clean_seq = [[None]]
    Alb.command_line_ui(test_in_args, alignments.get_one("m p pr"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "73b5d11dd25dd100648870228ab10d3d"

    test_in_args.clean_seq = [['strict', 'X']]
    Alb.command_line_ui(test_in_args, Alb.AlignBuddy(resource("ambiguous_dna_alignment.fa")), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "6755ea1408eddd0e5f267349c287d989"


# ##################### '-cta', '--concat_alignments' ###################### ##
def test_concat_alignments_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.concat_alignments = [[]]

    tester = Sb.SeqBuddy(resource("Cnidaria_pep.nexus"))
    Sb.pull_recs(tester, "Ccr|Cla|Hec")
    tester = Alb.AlignBuddy(str(tester))
    tester.alignments.append(tester.alignments[0])
    tester.set_format("genbank")
    Alb.command_line_ui(test_in_args, Alb.make_copy(tester), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "d21940f3dad2295dd647f632825d8541"

    test_in_args.concat_alignments = [["(.).(.)-Panx(.)"]]
    Alb.command_line_ui(test_in_args, Alb.make_copy(tester), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "5ac908ebf7918a45664a31da480fda58"

    test_in_args.concat_alignments = [["...", "Panx.*"]]
    Alb.command_line_ui(test_in_args, Alb.make_copy(tester), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "e754350b0397cf54f531421d1e85774f"

    test_in_args.concat_alignments = [[3, "Panx.*"]]
    Alb.command_line_ui(test_in_args, Alb.make_copy(tester), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "e754350b0397cf54f531421d1e85774f"

    test_in_args.concat_alignments = [[-9, "Panx.*"]]
    Alb.command_line_ui(test_in_args, Alb.make_copy(tester), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "9d2886afc640d35618754e05223032a2"

    test_in_args.concat_alignments = [[3, 3]]
    Alb.command_line_ui(test_in_args, Alb.make_copy(tester), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "4e4101f9b5a6d44d524a9783a8c4004b"

    test_in_args.concat_alignments = [[3, -3]]
    Alb.command_line_ui(test_in_args, Alb.make_copy(tester), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "5d9d9ac8fae604be74c436e5f0b5b6db"

    Alb.command_line_ui(test_in_args, alignments.get_one("p o g"), skip_exit=True)
    out, err = capsys.readouterr()
    assert "Please provide at least two alignments." in err

    test_in_args.concat_alignments = [["foo"]]
    Alb.command_line_ui(test_in_args, alignments.get_one("m p c"), skip_exit=True)
    out, err = capsys.readouterr()
    assert "No match found for record" in err


# ##################### '-con', '--consensus' ###################### ##
def test_consensus_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.consensus = True
    Alb.command_line_ui(test_in_args, alignments.get_one("m d s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "7b0aa3cca159b276158cf98209be7dab"

    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "89130797253646e61b78ab7d91ad3fd9"


# ##################### '-dr', '--delete_records' ###################### ##
def test_delete_records_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.delete_records = [["α[1-5]", "β[A-M]"]]
    Alb.command_line_ui(test_in_args, alignments.get_one("m d s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "de5beddbc7f0a7f8e3dc2d5fd43b7b29"
    assert string2hash(err) == "31bb4310333851964015e21562f602c2"

    test_in_args.delete_records = [["α[1-5]", "β[A-M]", 4]]
    Alb.command_line_ui(test_in_args, alignments.get_one("m d s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(err) == "ce6c9b29c95ba853eb444de5c71aeca9"

    test_in_args.delete_records = [["foo"]]
    Alb.command_line_ui(test_in_args, alignments.get_one("m d s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert "No sequence identifiers match 'foo'\n" in err


# ##################### '-et', '--enforce_triplets' ###################### ##
def test_enforce_triplets_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.enforce_triplets = True
    Alb.command_line_ui(test_in_args, alignments.get_one("o d g"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "4fabe926e9d66c40b5833cda32506f4a"

    Alb.command_line_ui(test_in_args, alignments.get_one("m p c"), skip_exit=True)
    out, err = capsys.readouterr()
    assert "Nucleic acid sequence required, not protein." in err


# ##################### '-er', '--extract_range' ###################### ##
def test_extract_range_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.extract_range = [10, 110]
    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "3929c5875a58e9a1e64425d4989e590a"

    test_in_args.extract_range = [110, 10]
    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "3929c5875a58e9a1e64425d4989e590a"

    test_in_args.extract_range = [-110, 10]
    with pytest.raises(SystemExit):
        Alb.command_line_ui(test_in_args, alignments.get_one("m p s"))
    out, err = capsys.readouterr()
    assert err == "ValueError: Please specify positive integer indices\n"


# ###############################  '-li', '--list_ids' ############################## #
def test_list_ids(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.list_ids = [False]
    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "f087f9c1413ba66c28fb0fccf7c974e6"

    test_in_args.list_ids = [3]
    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "4d85249a1f187d38d411a78ced65a98c"


# #################################### '-lc', '--lowercase' ################################### #
def test_lowercase_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.lowercase = True
    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "00661f7afb419c6bb8c9ac654af7c976"


# ##################### '-mf2a', '--map_features2alignment' ###################### ##
def test_map_features2alignment_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.mapfeat2align = [resource("Mnemiopsis_cds.gb")]
    Alb.command_line_ui(test_in_args, alignments.get_one("o d n"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "2d8b6524010177f6507dde387146378c"


# ###############################################  '-ns', '--num_seqs' ################################################ #
def test_num_seqs_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.num_seqs = True
    for alignbuddy in alignments.get_list("m d c pr psr s"):
        Alb.command_line_ui(test_in_args, alignbuddy, skip_exit=True)
        out, err = capsys.readouterr()
        assert out == "# Alignment 1\n8\n\n# Alignment 2\n21\n" or out == "# Alignment 1\n13\n\n# Alignment 2\n21\n"

    for alignbuddy in alignments.get_list("m p c pr psr s"):
        Alb.command_line_ui(test_in_args, alignbuddy, skip_exit=True)
        out, err = capsys.readouterr()
        assert out == "# Alignment 1\n20\n\n# Alignment 2\n13\n" or out == "# Alignment 1\n13\n\n# Alignment 2\n21\n"

    for alignbuddy in alignments.get_list("o p c pr psr s"):
        Alb.command_line_ui(test_in_args, alignbuddy, skip_exit=True)
        out, err = capsys.readouterr()
        assert out == "13\n"


# ###############################################  '-oi', '--order_ids' ################################################ #
def test_order_ids_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.order_ids = [False]
    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "0bce6aeaab76feda1aea7f5e79608c72"

    test_in_args.order_ids = ['rev']
    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "f87f78dc9d7a0b76854f15c52130e3a7"


# ##################### '-pr', '--pull_records' ###################### ##
def test_pull_records_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.pull_records = [["α[1-5]$", "β[A-M]"]]
    Alb.command_line_ui(test_in_args, alignments.get_one("m d s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "2de557d6fd3dc6cd1bf43a1995392a4c"
    assert err == ""


# ##################### '-d2r', '--transcribe' ###################### ##
def test_transcribe_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.transcribe = True
    Alb.command_line_ui(test_in_args, alignments.get_one("o d n"), skip_exit=True)
    out, err = capsys.readouterr()

    assert string2hash(out) == "e531dc31f24192f90aa1f4b6195185b0"

    with pytest.raises(SystemExit):
        Alb.command_line_ui(test_in_args, alignments.get_one("o r n"))
    out, err = capsys.readouterr()
    assert err == "TypeError: DNA sequence required, not IUPACAmbiguousRNA().\n"


# #################################### '-uc', '--uppercase' ################################### #
def test_uppercase_ui(capsys):
    test_in_args = deepcopy(in_args)
    test_in_args.uppercase = True
    Alb.command_line_ui(test_in_args, alignments.get_one("m p s"), skip_exit=True)
    out, err = capsys.readouterr()
    assert string2hash(out) == "6f3f234d796520c521cb85c66a3e239a"
