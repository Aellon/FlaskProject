import rdflib
from rdflib import URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, FOAF, RDFS
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery
from collections import OrderedDict


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
        ex = Namespace("http://example.org/")
        domain = "http://example.org/"
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

        self.la = relationList

        for c in concepts:
            if(conceptsMap[c] == 'True'):
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
            self.graph.add((pred, RDFS.domain, ex.RootConcept))
            self.graph.add((pred, RDFS.range, ex.RootConcept))


        for r in stmtList:
            s = domain + r.subject
            p = domain + r.predicate
            o = domain + r.object

            sub = URIRef(s)
            pred = URIRef(p)
            obj = URIRef(o)

            self.graph.add((sub, pred, obj))

        #print(self.graph.serialize(destination="lol.ttl", format="turtle"))
        return self.graph



        #self.graph.parse('lol.ttl', format="turtle")
        #print(relationList[0].object)







#G = GraphGenerator('seed_concepts.txt', 'seed_relationships.txt')
#G.generateGraph()