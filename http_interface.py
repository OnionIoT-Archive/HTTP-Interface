import amqp_rpc as rpc
from bottle import Bottle, run, request, response
import json

app = Bottle()

@app.hook('after_request')
def enable_cors():
    """
    You need to add some headers to each request.
    Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
 

@app.get('/api/devices/<deviceId>/<path:path>')
def getStatus(deviceId=None, path=None):
    if deviceId == None:
        return {"error":"invalid device"};
    path = '/'+path
    
    data = {}
    data['deviceId'] = deviceId
    data["path"] = path
    data["verb"] = "GET"
    result =  rpc.call('IF_CALL_FUNCTION', data )
    result = {'error': result}
    response.set_header('Content-Type', 'application/json')
    return json.dumps(result)

@app.post('/api/devices/<deviceId>/<path:path>')
def getStatus(deviceId=None, path=None):
    if deviceId == None:
        return {"error":"invalid device"};
    path = '/'+path
    
    data = {}
    data['deviceId'] = deviceId
    data["path"] = path
    data["verb"] = "POST"
    postParams = {}
    if "form-data" in request.content_type:
        for key in request.forms:
            postParams[key] = request.forms.get(key)
    elif "application/json" in request.content_type:
        postParams = request.json
    elif "text/plain" in request.content_type:
        try:
            postParams = json.loads(request.body.read())
        except Exception as e:
            return {"Error": str(e)}
    else:
        try:
            for key in request.forms:
                postParams[key] = request.forms.get(key)
        except Exception as e:
            return {"Error": str(e)}

    data["postParams"] = postParams

    result =  rpc.call('IF_CALL_FUNCTION', data )
    result = {'error': result}
    response.set_header('Content-Type', 'application/json')
    return json.dumps(result)


if __name__ == "__main__":
    run(app, host='0.0.0.0', port=80, debug=True, server='paste')
    print "started..."
