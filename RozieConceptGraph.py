import flask
from flask_restful import Api, Resource, reqparse, fields, marshal
import rdflib
from rdflib import Namespace, URIRef
from rdflib.plugins.sparql import prepareQuery
from collections import OrderedDict
import FileOperations
from rdflib.namespace import RDF, FOAF, RDFS
import os.path

app = flask.Flask(__name__, static_url_path="")
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
    'object': fields.String,
}

status_fields = {
    'status': fields.String
}

n = Namespace("http://example.org/")
rdfNs = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
rdfsNs = "http://www.w3.org/2000/01/rdf-schema#"
foafNs = "http://xmlns.com/foaf/0.1/"
domain = "http://example.org/"

g = rdflib.Graph()

if os.path.exists('Rozie.ttl'):
    g.parse('Rozie.ttl', format="turtle")
else:
    generator = FileOperations.GraphGenerator('seed_concepts.txt', 'seed_relationships.txt')
    g = generator.generateGraph()
    g.serialize(destination="Rozie.ttl", format="turtle")
    print("Graph generated...!")


class GraphAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(GraphAPI, self).__init__()

    def get(self):
        statements = []
        query = prepareQuery('SELECT ?a ?b ?c WHERE{?a ?b ?c}')
        results = g.query(query)

        for row in results:
            subject = row.a
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
        super(RelationsAPI, self).__init__()

    def get(self, concept, predicate, obj):
        sub = domain + concept
        pre = domain + predicate
        predUri = URIRef(pre)
        subUri = URIRef(sub)
        relations = []
        query = prepareQuery('SELECT ?a ?b ?c WHERE{?a ?b ?c}')

        if predicate == "all":
            results = g.query(query, initBindings={'a': subUri})
        else:
            results = g.query(query, initBindings={'a': subUri, 'b': predUri})

        if obj == 'no':
            for row in results:
                relation = OrderedDict()
                predicate = row.b
                relation['predicate'] = predicate
                relations.append(relation)
            return {'relations': marshal(relations, relation_fields)}
        else:
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
                          "WHERE {<http://example.org/%s> <http://example.org/%s>* ?c}" % (concept, predicate))

        for row in results:
            objct = OrderedDict()
            value = row.c
            objct['object'] = value
            objects.append(objct)
        return {'relations': marshal(objects, object_fields)}


class RelationsAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(RelationsAPI, self).__init__()

    def get(self, concept, predicate, obj):
        sub = domain + concept
        pre = domain + predicate
        predUri = URIRef(pre)
        subUri = URIRef(sub)
        relations = []
        query = prepareQuery('SELECT ?a ?b ?c WHERE{?a ?b ?c}')

        if predicate == "all":
            results = g.query(query, initBindings={'a': subUri})
        else:
            results = g.query(query, initBindings={'a': subUri, 'b': predUri})
        if obj == 'no':
            for row in results:
                relation = OrderedDict()
                predicate = row.b
                relation['predicate'] = predicate
                relations.append(relation)
            return {'relations': marshal(relations, relation_fields)}
        else:
            for row in results:
                relation = OrderedDict()
                predicate = row.b
                obj = row.c
                relation['predicate'] = predicate
                relation['object'] = obj
                relations.append(relation)
            return {'relations': marshal(relations, relation_object_fields)}


class ParentsAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(ParentsAPI, self).__init__()

    def get(self):
        objects = []
        results = g.query("SELECT ?c WHERE {?c <http://www.w3.org/2000/01/rdf-schema#subClassOf> "
                          "<http://example.org/RootConcept>}")
        for row in results:
            objct = OrderedDict()
            value = row.c
            objct['parent'] = value
            objects.append(objct)
        return {'parents': marshal(objects, {'parent': fields.String})}


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
        statusList = []
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
            return {'status': marshal(statusList, status_fields)}
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
            'ex': n,
            'RDF': rdfNs,
            'RDFS': rdfsNs,
            'foaf': foafNs,
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
        statusList = []
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
            'ex': n,
            'RDF': rdfNs,
            'RDFS': rdfsNs,
            'foaf': foafNs,
        }[name]


# Return whole graph.
api.add_resource(GraphAPI, '/Rozie/graph', endpoint='graph')
# Return relations of the given concept, relation type can be given also can return the objects of respective relation.
api.add_resource(RelationsAPI, '/Rozie/relations/<string:concept>/<string:predicate>/<string:obj>',
                 endpoint='relations')
# Return objects of a given concept respective to the given relation.
api.add_resource(ResolverAPI, '/Rozie/resolve/<string:concept>/<string:predicate>', endpoint='resolve')
# Add and Delete concepts.
api.add_resource(UpdateConceptAPI, '/Rozie/update/concepts', endpoint='updateConcept')
# Add and Delete relations.
api.add_resource(UpdateRelationAPI, '/Rozie/update/relations', endpoint='updateRelation')
# Return all parent nodes.
api.add_resource(ParentsAPI, '/Rozie/graph/parents', endpoint='parent')

if __name__ == '__main__':
    app.run(debug=True)
