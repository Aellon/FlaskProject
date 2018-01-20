from collections import OrderedDict
import rdflib
from rdflib import URIRef, Namespace
from rdflib.namespace import RDF, RDFS


class Statement:
    def __init__(self, subject, predicate, objct):
        self.subject = subject
        self.object = objct
        self.predicate = predicate


class GraphGenerator:
    def __init__(self, file1, file2):
        self.filePath1 = file1
        self.filePath2 = file2

    def generateGraph(self):
        ex = Namespace("http://example.org/#")
        domain = "http://example.org/#"
        self.graph = rdflib.Graph()
        self.conceptFile = open(self.filePath1,'r')
        self.relationFile = open(self.filePath2,'r')
        conceptsMap = OrderedDict()
        relationList = []
        stmtList = []
        concepts = []

        for line in self.conceptFile:
             verbs = line.split('|')
             conceptsMap[verbs[0].replace(" ","")] = verbs[2].rstrip()
             concepts.append(verbs[0].replace(" ",""))

        for line in self.relationFile:
            verbs = line.split('|')
            relationList.append(Statement(verbs[0].replace(" ",""), verbs[2].replace(" ",""), verbs[4].replace(" ","").rstrip()))
            stmtList.append(Statement(verbs[0].replace(" ",""), verbs[2].replace(" ",""), verbs[4].replace(" ","").rstrip()))

        self.graph.add((ex.RootConcept, RDF.type, RDFS.Class))
        self.graph.add((ex.Concept, RDFS.subClassOf, ex.RootConcept))

        for c in concepts:
            if conceptsMap[c] == 'True':
                uri = domain + c
                cnspt = URIRef(uri)
                self.graph.add((cnspt, RDFS.subClassOf, ex.RootConcept))
            else:
                uri = domain + c
                cnspt = URIRef(uri)
                self.graph.add((cnspt, RDFS.subClassOf, ex.Concept))

        for rel in relationList:
            p = domain + rel.predicate
            pred = URIRef(p)
            self.graph.add((pred, RDF.type, RDF.Property))
            self.graph.add((pred, RDFS.domain, ex.Concept))
            self.graph.add((pred, RDFS.range, ex.Concept))

        for r in stmtList:
            s = domain + r.subject
            p = domain + r.predicate
            o = domain + r.object
            sub = URIRef(s)
            pred = URIRef(p)
            obj = URIRef(o)
            self.graph.add((sub, pred, obj))
        return self.graph
