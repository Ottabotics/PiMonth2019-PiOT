import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import sys
import time
import datetime

def printUsage():
    print("\nUsage: python oc.py (app_id) (api_key) [-json]\n\n where -json will cause the program to spit out the raw JSON data from the API.  Omitting it gives you the regular interface.")

def formatData(jsonData):
    '''
    (dict)->(dict)
    Formats the incoming JSON object into a nicer printable one.
    '''

    return json.dumps(jsonData, indent=4)

def tripsToString(jsonData):
    '''
    (dict)->none
    Takes JSON object and from it, prints upcoming trips.
    '''

    obj = jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]

    print("\nUpcoming trips for stop #" + str(jsonData['GetRouteSummaryForStopResult']["StopNo"]) + " (" + str(jsonData['GetRouteSummaryForStopResult']["StopDescription"]) + "): \n\n")

    # Test: is "Route" a list or a dict?  If dict, stop serviced by one route.  If list, stop serviced by multiple routes.
    if(isinstance(obj, list)):
        numRoutes = len(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"])
    else:
        numRoutes = 1;

    if(numRoutes == 1):

        numTrips = len(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]["Trips"]["Trip"])

        print("\tRoute " + str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]["RouteNo"]) + " " + str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]["RouteHeading"]) + ":\n\n")

        for i in range(0, numTrips):
            print("\t\tto " + str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]["Trips"]["Trip"][i]["TripDestination"]) + " - at " + str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]["Trips"]["Trip"][i]["TripStartTime"]))
            print("\n")

        if(numTrips == 0):
            print("\t\tNothing right now.\n\n")

    elif(numRoutes > 1):

        #print("Multiple routes\n")

        for i in range(0, numRoutes):

            if 'Trips' in jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]:
                numTrips = len(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]["Trips"])
            else:
                numTrips = 0

            print("\tRoute " + str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]["RouteNo"]) + " " + str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]["RouteHeading"]) + ":\n\n")

            for j in range(0, numTrips):
                print("\t\tto " + str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]["Trips"][j]["TripDestination"]) + " - at " + str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]["Trips"][j]["TripStartTime"]))
                print("\n")

            if (numTrips == 0):
                print("\t\tNothing right now.\n\n")

def assessSituation(jsonData):

    timeFromNow = getNextBusTime(jsonData)

    if (timeFromNow <= 5) and (timeFromNow >= 2):
        state = 'SOON'
    elif (timeFromNow == 1):
        state = 'IMMINENT'
    else:
        state = 'NOT SOON'

    return state


def getNextBusTime(jsonData):

    if(datetime.datetime.now().hour == 0):
        currentTime = int(str(24) + str(datetime.datetime.now().minute))  #Must correct: between 12AM and 1AM, use hour "24" rather than "0"
    elif(datetime.datetime.now().hour == 1):
        currentTime = int(str(25) + str(datetime.datetime.now().minute))  # Must correct: between 1AM and 2AM, use hour "25" rather than "1"
    else:
        currentTime = int(str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute))

    if isinstance(jsonData["GetRouteSummaryForStopResult"]["Routes"]["Route"], list):
        numRoutes = len(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"])
    else:
        numRoutes = 1;

    if(numRoutes == 1):
        if 'Trips' in jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]:
            numTrips = len(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]["Trips"]["Trip"])
        else:
            numTrips = 0
            currNextTime = 0

        nextTime = 25000

        for i in range(0, numTrips):

            currNextTime = int(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"]["Trips"]["Trip"][i]["TripStartTime"].replace(':',''))
            if (currentTime < currNextTime < nextTime) and (numTrips > 0):
                nextTime = currNextTime

    else:

        nextTime = 25000

        for i in range(0, numRoutes):



            if 'Trips' in jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]:
                numTrips = len(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]["Trips"])

                for j in range(0, numTrips):
                    currNextTime = int(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]["Trips"][j]["TripStartTime"].replace(':', ''))
                    #print(str(jsonData['GetRouteSummaryForStopResult']["Routes"]["Route"][i]["RouteNo"]) + ":  " + str(
                    #    currNextTime) + "," + str(nextTime) + "," + str(numTrips))
                if (currentTime < currNextTime < nextTime) and (numTrips > 0):
                    nextTime = currNextTime

            else:
                numTrips = 0
                currNextTime = 0


    print("next time " + str(nextTime) + " and curr time " + str(currentTime))

    timeFromNow = nextTime - currentTime

    return timeFromNow

if (len(sys.argv) != 3) and len(sys.argv) != 4:
    printUsage()
    sys.exit(-1)

url = "https://api.octranspo1.com/v1.2/GetNextTripsForStopAllRoutes" #URL to query

#appId = input("Please enter your app ID.")
appId = sys.argv[1]

#apiKey = input("Please enter your OC Transpo API key.")
apiKey = sys.argv[2]



#stopNumber = input("Please type in the stop number.")
stopNumber = 6783

vals = {'appID'  : appId,
        'apiKey' : apiKey,
        'stopNo' : stopNumber,
        'format' : 'json'} #Parameters to pass to URL

data = urllib.parse.urlencode(vals) #Some parsing and encoding magic

data = data.encode('ascii')

req= urllib.request.Request(url, data)

with urllib.request.urlopen(req) as response:
    rawData = json.loads(response.read())

cleanData = formatData(rawData)

state = 'UNDEFINED'

if(len(sys.argv) == 3):
    while(1):

        req = urllib.request.Request(url, data)

        with urllib.request.urlopen(req) as response:
            rawData = json.loads(response.read())

        print(assessSituation(rawData))
        time.sleep(10)
elif(len(sys.argv) == 4 and sys.argv[3] == '-json'):
    print(formatData(rawData))

# Message Ivor for app ID and API key
