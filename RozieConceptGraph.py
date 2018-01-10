from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
import rdflib
from rdflib import URIRef, BNode, Literal, Namespace
from rdflib.plugins.sparql import prepareQuery
from collections import OrderedDict
from FileOperations import GraphGenerator, Statement
from rdflib.namespace import RDF, FOAF, RDFS
import os.path


app = Flask(__name__, static_url_path="")
api = Api(app)

task_fields = {
    'subject': fields.String,
    'predicate': fields.String,
    'object': fields.String,
}

relation_fields = {
'predicate': fields.String,
}

object_fields = {
'object': fields.String,
}

relation_object_fields = {
'predicate': fields.String,
'object' : fields.String,
}

status_fields = {
    'status' : fields.String
}
g=rdflib.Graph()


if os.path.exists('Rozie.ttl'):
    g.parse('Rozie.ttl', format="turtle")
else:
    generator = GraphGenerator('seed_concepts.txt', 'seed_relationships.txt')
    g = generator.generateGraph()

    g.serialize(destination="Rozie.ttl", format="turtle")
    print("Graph generated...!")



n = Namespace("http://example.org/")
rdfNs = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
rdfsNs = "http://www.w3.org/2000/01/rdf-schema#"
foafNs = "http://xmlns.com/foaf/0.1/"
domain = "http://example.org/"

#for s,p,o in g.triples( (None, n.Typeof, n.Location) ):
  # print ("%s is a Type of Location"%s)

class GraphAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, help='No task title provided', location='json')
        self.reqparse.add_argument('description', type=str, default="", location='json')
        super(GraphAPI, self).__init__()

    def get(self):
        statements = []
        query = prepareQuery('SELECT ?a ?b ?c WHERE{?a ?b ?c}')
        results = g.query(query)

        for row in results:
            subject  = row.a
            predicate = row.b
            objct = row.c
            statement = OrderedDict()

            statement['subject'] = subject
            statement['predicate'] = predicate
            statement['object'] = objct

            statements.append(statement)

        return {'graph': marshal(statements, task_fields)}


class RelationsAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, help='No task title provided', location='json')
        self.reqparse.add_argument('description', type=str, default="", location='json')
        super(RelationsAPI, self).__init__()

    def get(self, concept, predicate, obj):
        sub = domain + concept
        pre = domain + predicate
        predUri = URIRef(pre)
        subUri = URIRef(sub)
        relations = []

        query = prepareQuery('SELECT ?a ?b ?c WHERE{?a ?b ?c}')

        if(predicate == "all"):
            results = g.query(query, initBindings={'a': subUri})
        else :
            results = g.query(query, initBindings={'a':subUri, 'b':predUri})

        if obj == 'no':
            for row in results:
                relation = OrderedDict()
                predicate = row.b
                relation['predicate'] = predicate
                relations.append(relation)

            return {'relations': marshal(relations, relation_fields)}
        else :
            for row in results:
                relation = OrderedDict()
                predicate = row.b
                obj = row.c
                relation['predicate'] = predicate
                relation['object'] = obj
                relations.append(relation)

            return {'relations': marshal(relations, relation_object_fields)}

class ResolverAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(ResolverAPI, self).__init__()

    def get(self, concept, predicate):
        objects = []
        results = g.query("SELECT ?c "
               "WHERE {<http://example.org/%s> <http://example.org/%s>* ?c}"%(concept,predicate))

        for row in results:
            objct = OrderedDict()
            value = row.c
            objct['object'] = value
            objects.append(objct)

        return {'relations': marshal(objects, object_fields)}


class UpdateConceptAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('option', type=str, location='json')
        self.reqparse.add_argument('subject', type=str, help='No task subject provided', location='json')
        self.reqparse.add_argument('predicate', type=str, default="", location='json')
        self.reqparse.add_argument('objct', type=str, default="", location='json')
        self.reqparse.add_argument('subNs', type=str, default="", location='json')
        self.reqparse.add_argument('predNs', type=str, default="", location='json')
        self.reqparse.add_argument('objctNs', type=str, default="", location='json')
        super(UpdateConceptAPI, self).__init__()


    def post(self):
        args = self.reqparse.parse_args()
        sub = args['subject'];
        opt = args['option']
        statusList =[]
        status = {}
        subNs = self.getNamespace(args['subNs']) + sub;
        subUri = URIRef(subNs)


        if opt == 'add':
            pred = args['predicate'];
            obj = args['objct'];
            predNs = self.getNamespace(args['predNs']) + pred;
            objNs = self.getNamespace(args['objctNs']) + obj;
            predUri = URIRef(predNs)
            objRri = URIRef(objNs)

            g.add((subUri, predUri, objRri))
            g.serialize(destination="Rozie.ttl", format="turtle")
            status['status'] = "Successfully Updated"
            statusList.append(status)
            return {'status': marshal(statusList,status_fields)}

        if opt == 'delete':
            g.remove((subUri, None, None))
            g.serialize(destination="Rozie.ttl", format="turtle")
            status['status'] = "Successfully deleted"
            statusList.append(status)
            return {'status': marshal(statusList, status_fields)}

        status['status'] = "Not a valid option."
        statusList.append(status)
        return {'status': marshal(statusList, status_fields)}

    def getNamespace(self, name):
        return {
            'ex' : n,
            'RDF' : rdfNs,
            'RDFS' : rdfsNs,
            'foaf' : foafNs,
        }[name]


class UpdateRelationAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('option', type=str, help='No task subject provided', location='json')
        self.reqparse.add_argument('subject', type=str, default="", location='json')
        self.reqparse.add_argument('domain', type=str, default="", location='json')
        self.reqparse.add_argument('range', type=str, default="", location='json')
        self.reqparse.add_argument('subNs', type=str, default="", location='json')
        self.reqparse.add_argument('domNs', type=str, default="", location='json')
        self.reqparse.add_argument('rnNs', type=str, default="", location='json')

        super(UpdateRelationAPI, self).__init__()


    def post(self):
        args = self.reqparse.parse_args()
        opt = args['option'];
        sub = args['subject'];
        statusList =[]
        status = {}
        subNs = self.getNamespace(args['subNs']) + sub;
        subUri = URIRef(subNs)

        if opt == 'add':
            domain = args['domain'];
            rng = args['range'];
            objNs = self.getNamespace('RDF') + 'Property';
            domainNs = self.getNamespace(args['domNs']) + domain;
            rnNs = self.getNamespace(args['rnNs']) + rng;
            predNs = self.getNamespace('RDF') + 'Type';

            predUri = URIRef(predNs)
            objRri = URIRef(objNs)
            domUri = URIRef(domainNs)
            rngUri = URIRef(rnNs)

            g.add((subUri, predUri, objRri))
            g.add((subUri, RDFS.domain, domUri))
            g.add((subUri, RDFS.range, rngUri))
            g.serialize(destination="Rozie.ttl", format="turtle")
            status['status'] = "Successfully Updated"
            statusList.append(status)

            return {'status': marshal(statusList, status_fields)}

        if opt == 'delete':

            g.remove((subUri, None, None))
            g.serialize(destination="Rozie.ttl", format="turtle")
            status['status'] = "Successfully Deleted"
            statusList.append(status)

            return {'status': marshal(statusList, status_fields)}

        status['status'] = "Option undefined"
        statusList.append(status)
        return {'status': marshal(statusList, status_fields)}

    def getNamespace(self, name):
        return {
            'ex' : n,
            'RDF' : rdfNs,
            'RDFS' : rdfsNs,
            'foaf' : foafNs,
        }[name]


api.add_resource(GraphAPI, '/Rozie/graph', endpoint='graph')
api.add_resource(RelationsAPI, '/Rozie/relations/<string:concept>/<string:predicate>/<string:obj>', endpoint='relations')
api.add_resource(ResolverAPI, '/Rozie/resolve/<string:concept>/<string:predicate>', endpoint='resolve')
api.add_resource(UpdateConceptAPI, '/Rozie/update/concepts', endpoint='updateConcept')
api.add_resource(UpdateRelationAPI, '/Rozie/update/relations', endpoint='updateRelation')


if __name__ == '__main__':
    app.run(debug=True)
