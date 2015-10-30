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
from rdflib import Graph, RDFS, BNode
import sys
import argparse

def par_graph_name(opts):
    return opts.infile + ".s.ttl"

def ancestors(n: str, parents: dict, paths: dict) -> list:
    """ Determine the path(s) to the root for node n
    :param n: Target node
    :param parents: parents dictionary
    :param paths: known paths
    :return: list of lists of paths
    """
    if n in paths:
        return paths[n]
    if n in parents:
        rval = []
        for p in parents[n]:
            for al in ancestors(p, parents, paths):
                rval.append([p] + al)
    else:
        rval = [[]]
    return rval


def write_results(outf, opts: argparse.Namespace, paths: dict) -> None:
    for k, ps in paths.items():
        outf.write("\n%s:\n " % k)
        outf.write('\n'.join(['\t' + str(p) for p in ps]))


def parents_graph(g: Graph, opts: argparse.Namespace) -> dict:
    rval = dict()
    if opts.save:
        par_graph = Graph()
    for s, o in g.subject_objects(RDFS.subClassOf):
        if not isinstance(o, BNode):
            rval.setdefault(str(s), []).append(str(o))
            if opts.save:
                par_graph.add((s, RDFS.subClassOf, o))
    if opts.infile:
        pass
    if opts.save:

    return rval


def eval_paths(opts: argparse.Namespace):

    def o_print(txt: str, end='\n'):
        if opts.outfile:
            print(txt, end=end)

    o_print("Parsing: " + opts.infile)
    g = Graph()
    g.parse(opts.infile, format=opts.infile_format)

    o_print("Processing...", end='')
    parents = parents_graph(g, opts)
    paths = dict()

    if not opts.node:
        for s in parents.keys():
            paths[s] = ancestors(s, parents, paths)
    else:
        for n in opts.node:
            paths[n] = ancestors(n, parents, paths)

    o_print("%d paths processed" % len(paths))
    if opts.outfile:
        o_print("Writing " + opts.outfile + "...", end='')
    outf = open(opts.outfile, 'w') if opts.outfile else sys.stdout
    write_results(outf, opts, paths)
    o_print("Done")


def main(args):
    """ Compute the paths from a node (or nodes) to the root.
    """
    parser = argparse.ArgumentParser(description="Determine root paths")
    parser.add_argument("infile", help="Input OWL file")
    parser.add_argument("-if", "--infile_format", help="Input file format", default="xml")
    parser.add_argument("-o", "--outfile", help="Output file")
    parser.add_argument("-n", "--node", help="Node(s) to create paths for. If absent, do all nodes", nargs="*")
    parser.add_argument("-b", "--base", help="Base URI for node(s)")
    parser.add_argument("-s", "--save", help="Save parents graph", action="store_true")
    parser.add_argument("-u", "--use", help="Use parents graph", action="store_true")
    opts = parser.parse_args(args)
    eval_paths(opts)


if __name__ == '__main__':
    main(sys.argv[1:])
