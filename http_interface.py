import amqp_rpc as rpc
#from bottle import Bottle, run, request, response
import json

from flask import Flask, request, make_response

app = Flask(__name__)


with open('/etc/onionConfig.json') as f:
    config = json.load(f)['API_SERVER']

def callRemoteFunction(params):
    payload = {}
    payload['path'] = params['path']
    payload['verb'] = params['verb']
    payload['deviceId'] = params['deviceId']
    path = params['path']
    verb = params['verb']
    deviceId = params['deviceId']

    result = rpc.call('DB_GET_PROCEDURE', payload)
    if result != None:
        fid = result["functionId"]
        if params['verb'].upper() == "POST":
            postParams = params['postParams'] 
            params = []
            for p in result['postParams']:
                temp = str(postParams[p])
                params.append(str(temp.replace(',','.').replace(';',':')))
            cmd = "%s;%s"%(fid,','.join(params))
        else:
            postParams = None
            cmd = fid

        print '%s < %s'%(deviceId, cmd)
        rpc.call('IF_MQTT_SEND', {'deviceId':deviceId, 'cmd':cmd})

        rpc.call('DB_ADD_HISTORY', {
            'deviceId': deviceId,
            'action': "%s: %s"%(verb, path),
            'payload': json.dumps(postParams)
            })
    else:
        return "endpoint cannot be found"

def callRemoteFunctionV2(params):
    payload = {}
    payload['path'] = params['path']
    payload['verb'] = params['verb']
    payload['deviceId'] = params['deviceId']
    path = params['path']
    verb = params['verb']
    deviceId = params['deviceId']

    result = rpc.call('DB_GET_PROCEDURE', payload)
    postParams = []
    if result != None:
        fid = result["functionId"]
        if params['verb'].upper() == "POST":
            for p in result['postParams']:
                temp = str(params['postParams'][p])
                postParams.append(temp)



        rpc.call('DB_ADD_HISTORY', {
            'deviceId': deviceId,
            'action': "%s: %s"%(verb, path),
            'payload': json.dumps(postParams)
            })

        return rpc.call('IF_DEVICE_SEND', {'deviceId':deviceId, 'functionId':fid, 'postParams': postParams})
    else:
        return "endpoint cannot be found"



@app.route('/<version>/devices/<deviceId>/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def onApiCall(version='v1', deviceId=None, path=None):
    if deviceId == None:
        return {"error":"invalid device id"};

    data = {}
    data['deviceId'] = deviceId
    data["path"] = '/'+path
    data["verb"] = request.method


    print request.headers['Content-Type']

    if request.method == 'OPTIONS': 
        print "on options"
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        return response

    elif request.method == 'GET': 
        pass
    
    elif request.method == 'POST': 
        postParams = {}
        if "form-data" in request.headers['Content-Type']:
            for key in request.form:
                postParams[key] = request.form[key]

        elif "application/json" in request.headers['Content-Type']:
            postParams = request.data
        else:
            try:
                postParams = json.loads(request.data)
            except Exception as e:
                response = make_response(json.dumps({"error": str(e)}))
                response.headers['Content-Type'] = 'application/json'
                response.headers['Access-Control-Allow-Origin'] = '*'
                return response
  
        data["postParams"] = postParams

    if version == "v1":
        result =  callRemoteFunction(data)
    elif version == "v2":
        result =  callRemoteFunctionV2(data)
    else:
        result = "API version not supported"

    result = {'error': result}

    response = make_response(json.dumps(result))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == "__main__":
    app.run(host=config['SERVER_HOST'], port=config['SERVER_PORT'])
    print "started..."
