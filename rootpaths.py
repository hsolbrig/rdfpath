# -*- coding: utf-8 -*-
# Copyright (c) 2015, Mayo Clinic
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#     Neither the name of the <ORGANIZATION> nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
from rdflib import Graph, RDFS, BNode, URIRef, RDF, OWL
import sys
import argparse


class PathEvaluator:
    """ Path evaluator - given a graph and an optional set of starting nodes, create a set of paths according
    to the template below
    """
    template = "%(depth)d|%(sep)sNCIT%(text_path)s|%(node_name)s|N|%(lorf)sA||%(concept_cd)s||concept_cd|concept_dimension|concept_path|T|LIKE|%(sep)sNCIT%(text_path)s|%(text_path)s|@|||||||||"

    def __init__(self, opts: argparse.Namespace):
        self.opts = opts
        self.g = Graph()
        self.paths = dict()
        self._o_print("Parsing: " + opts.infile)
        self.g.parse(self.opts.infile, format=self.opts.infile_format)
        self.outf = None

    def calc_paths(self, n: URIRef) -> None:
        """ Determine the path(s) to the root for the supplied target node
        :param n: Target node
        """
        if n not in self.paths:
            rval = []
            for o in self.g.objects(n, RDFS.subClassOf):
                if not isinstance(o, BNode):
                    for al in self.calc_paths(o):
                        rval.append([o] + al)
            self.paths[n] = rval if len(rval) else [[]]
        return self.paths[n]

    @staticmethod
    def code_for(n: URIRef) -> str:
        # TODO: Use the RDFLib namespace/name utilities rather than this simplistic solution
        return str(n).split('#')[-1]

    def name_for(self, n: URIRef) -> str:
        if not self.opts.use_name:
            return self.code_for(n)
        names = list(self.g.objects(n, RDFS.label))
        if not len(names):
            print("Missing rdfs:label for %s" % self.code_for(n), file=sys.stderr)
        return str(names[0]) if len(names) else "UNKNOWN"

    def format_path(self, n: URIRef, path: list) -> str:
        sep = self.opts.sep
        return sep + sep.join([self.name_for(e) for e in reversed(path)]) + sep + self.name_for(n) + sep

    def gen_path(self, node: URIRef, path: str, outf) -> str:
        depth = len(path) + 1
        text_path = self.format_path(node, path)
        node_name = self.name_for(node)
        lorf = 'F' if len(list(self.g.subjects(RDFS.subClassOf, node))) else 'L'
        concept_cd = self.code_for(node)
        sep = self.opts.sep
        outf.write(self.template % vars() + '\n')

    def eval(self) -> None:
        """ Evaluate the paths in the graph, either using the set of nodes supplied in the input or all nodes in the graph
        """
        self._o_print("Generating paths...", end='')
        for node in self.opts.nodes if self.opts.nodes else set(self.g.subjects()):
            if not isinstance(node, BNode) and not (node, RDF.type, OWL.AnnotationProperty) in self.g:
                self.calc_paths(node)
        self._o_print("%d paths generated" % len(self.paths))
        self._o_print("%d non-empty paths" % len([e for e in self.paths if len(e) > 0]))

        self._o_print("Writing " + (self.opts.outfile if self.opts.outfile else "stdout"), end='')
        outf = open(self.opts.outfile, 'w') if self.opts.outfile else sys.stdout
        [[self.gen_path(k, path, outf) for path in paths] for k, paths in self.paths.items()]

    def _o_print(self, txt: str, end='\n') -> None:
        """ Print a message if we're not writing the actual data to stdout
        :param txt: message
        :param end: eol
        """
        if self.opts.outfile:
            print(txt, end=end)


def main(args):
    """ Compute the paths from a node (or nodes) to the root.
    """
    parser = argparse.ArgumentParser(description="Determine root paths")
    parser.add_argument("infile", help="Input OWL file")
    parser.add_argument("-if", "--infile_format", help="Input file format", default="xml")
    parser.add_argument("-o", "--outfile", help="Output file")
    parser.add_argument("-n", "--nodes", help="Node(s) to create paths for. If absent, do all nodes", nargs="*")
    parser.add_argument("--sep", help="Path separator", default="\\")
    parser.add_argument("-u", "--use_name", help="Use node name in paths instead of code", action="store_true")
    opts = parser.parse_args(args)
    PathEvaluator(opts).eval()


if __name__ == '__main__':
    main(sys.argv[1:])
