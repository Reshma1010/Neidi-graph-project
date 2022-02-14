
import os
from py2neo import Graph
import glob
import time

# In order to run the code on your local machine, please enter the Neo4J database credentials. (Line 162, function -> DbConnection())

global numOfNodes
global numOfRelationships


class Nodes():
    # Node class

    primaryNode = ""
    secondaryNodes = ""
    relationship = ""
    colorOfEdge = ""
    entityColor = ""
    entityStyle = ""
    entityType = ""

    def __init__(self, primaryNode, secondaryNode, relationship, color):
        self.primaryNode = primaryNode.replace(' ', '_')
        self.secondaryNodes = secondaryNode.replace(' ', '_')
        self.relationship = relationship
        self.colorOfEdge = color

    def setEntityColor(self, entityColor):
        self.entityColor = entityColor

    def setEntityStyle(self, entityStyle):
        self.entityStyle = entityStyle

    def setEntityType(self, entityColor):
        if entityColor == "grey":
            self.entityType = "Object_Entity"
        elif entityColor == "lightblue":
            self.entityType = "Action_Entity"
        elif entityColor == "thistle":
            self.entityType = "Property_Entity"
        else:
            self.entityType = "Object_Class_Entity"


def CreateEntityNodes(nodes):
    listOfEntityNodes = []
    for node in nodes:
        if node.entityType not in listOfEntityNodes and len(node.entityType) > 0:
            listOfEntityNodes.append(node.entityType)

    print("Entities: " + ', '.join(listOfEntityNodes))

    dbConn = DbConnection()
    for entityType in listOfEntityNodes:
        execution = dbConn.begin()
        graphQuery = "CREATE(n:" + entityType + "{Name:" + '"' + entityType + '"' + "})"
        execution.run(graphQuery)
        execution.commit()


def CreateRelationshipsWithEntityType(nodes):
    # creating relationship with Entity Type

    DistinctList = []

    dbConn = DbConnection()
    for n in nodes:
        if n.entityType is not '' and n.primaryNode not in DistinctList:
            execution = dbConn.begin()
            graphQuery = "MATCH (a:" + n.primaryNode + "), (b:" + n.entityType + ") WHERE a.Name = " + '"' + n.primaryNode + '"' + " AND b.Name = " + '"' + n.entityType + '"' + " CREATE (a)-[r:" + "entity_type" + "]->(b) RETURN r"
            execution.run(graphQuery)
            execution.commit()
            DistinctList.append(n.primaryNode)


def CreateRelationships(nodes):
    global numOfRelationships

    dbConn = DbConnection()
    for n in nodes:
        # creating normal relationships
        if n.secondaryNodes is not "":
            execution = dbConn.begin()
            graphQuery = "MATCH (a:" + n.primaryNode + "), (b:" + n.secondaryNodes + ") WHERE a.Name = " + '"' + n.primaryNode + '"' + " AND b.Name = " + '"' + n.secondaryNodes + '"' + " CREATE (a)-[r:" + n.relationship + "]->(b) RETURN r"
            numOfRelationships += 1
            execution.run(graphQuery)
            execution.commit()


def CreateNodes(nodes):
    global numOfNodes

    distinctNodes = []
    for allNodes in nodes:
        if allNodes.primaryNode not in distinctNodes:
            distinctNodes.append(allNodes.primaryNode)

        if allNodes.secondaryNodes not in distinctNodes and len(allNodes.secondaryNodes) > 1:
            distinctNodes.append(allNodes.secondaryNodes)

    dbConn = DbConnection()

    for n in distinctNodes:
        execution = dbConn.begin()
        graphQuery = "CREATE(n:" + n + "{Name:" + '"' + n + '"' + "})"
        # print(graphQuery)
        execution.run(graphQuery)
        execution.commit()
        numOfNodes += 1


def GetNodeInformation(line):
    # this method will return the node names, relationship type and color
    # header will not be read
    node1 = line.split("->")[0].lstrip().rstrip().replace('"', '')
    node2 = (line.split("->")[1]).split("[")[0].lstrip().rstrip().replace('"', '')
    label = line[line.find("label") + 7:line.find("color")].lstrip().rstrip().replace('"', '').replace("-", "_")
    color = line[line.find("color") + 7:line.find("]")].lstrip().rstrip().replace('"', '')
    myNode = Nodes(node1, node2, label, color)
    return myNode


def Worker(fileName):
    # this method will read the file (line by line).
    # create Node objects
    # save Node objects in a list

    file = open(fileName, "r")
    header = True

    # list of nodes
    nodes = []

    for line in file:
        if line.find("->") != -1 and header == False and len(line) > 2:
            nodes.append(GetNodeInformation(line))
        elif line.find("->") == -1 and header == False and len(line) > 2:
            nodeAvailable = False
            nodeName = line.split("[", 1)[0].lstrip().rstrip().replace('"', '')
            for everyNode in nodes:
                if everyNode.primaryNode == nodeName:
                    nodeAvailable = True
                    everyNode.setEntityColor(
                        line[line.find("color") + 7:line.find("style")].lstrip().rstrip().replace('"', ''))
                    everyNode.setEntityStyle(
                        line[line.find("style") + 5:line.find("]")].lstrip().rstrip().replace('"', ''))
                    everyNode.setEntityType(
                        line[line.find("color") + 7:line.find("style")].lstrip().rstrip().replace('"', ''))

            # if a node have no relationship
            if nodeAvailable == False:
                nodeObj = Nodes(nodeName, "", "", "")
                nodeObj.setEntityColor(
                    line[line.find("color") + 7:line.find("style")].lstrip().rstrip().replace('"', ''))
                nodeObj.setEntityStyle(line[line.find("style") + 5:line.find("]")].lstrip().rstrip().replace('"', ''))
                nodeObj.setEntityType(

                    line[line.find("color") + 7:line.find("style")].lstrip().rstrip().replace('"', ''))
                nodes.append(nodeObj)
                nodeAvailable = True
        elif header == True:
            # skip the row
            header = False

    # Executing the methods
    CreateNodes(nodes)
    CreateEntityNodes(nodes)
    CreateRelationships(nodes)
    CreateRelationshipsWithEntityType(nodes)


def DbConnection():
    global databaseName

    uri = "bolt://localhost:7687"
    userName = "neo4j"
    password = "qwerty123"
    db = Graph(uri, auth=(userName, password))

    try:
        db.run("Match () Return 1 Limit 1")
    except Exception as e:
        print(e)
        exit(1)
    return db


def DeleteCurrentNodes():
    execution = DbConnection().begin()
    graphQuery = "MATCH (n) DETACH DELETE n"
    execution.run(graphQuery)
    execution.commit()
    print("\n")
    print("***************************NEW SAMPLE FILE***************************")


def main():
    global numOfNodes
    global numOfRelationships
    # global databaseName

    # project starts running from here.

    for fileName in glob.glob("*.gv"):
        # databaseName = fileName.replace('.gv', '')

        #1. Right the file name which you want to test.
        #2. After the code is executed, check neo4j.
        #3. Check if neo4j have exact same number of nodes are mentioned in the .gv file.
        #4. Check same for relationships between nodes.

        if fileName == 'SituationModelExtended_Portable_Air_Conditioner2.gv':
            start = time.time()
            def DbConnection():
                global databaseName
                uri = "bolt://localhost:7687"
                userName = "neo4j"
                password = "qwerty123"
                db = Graph(uri, auth=(userName, password))
                try:
                    db.run("Match () Return 1 Limit 1")
                except Exception as e:
                    print(e)
                    exit(1)
                    return db
            # Create database

            DeleteCurrentNodes()

            numOfNodes = 0
            numOfRelationships = 0

            print("FileName = " + fileName)

            # passing the filepath to the worker method.
            Worker(os.getcwd().replace("\\", "/") + "/" + fileName)

            end = time.time()

            print("Number of Nodes Created: " + str(numOfNodes))
            print("Number of Nodes Relationships: " + str(numOfRelationships))
            print("Time of Execution (in seconds): " + str(end - start))

            exit(0)

if __name__ == "__main__":
    main()
