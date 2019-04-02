from flask import Flask, request, render_template
from flask import send_file, send_from_directory
import json
from flask_cors import CORS


PORT = 20255

app = Flask("xialou")
CORS(app,resources={r"/api/*": {"origins": "https://go.zrt.io"}})

@app.errorhandler(404)
def page_not_found(_):
    return "Page not found.", 404

@app.route("/", methods=["GET"])
def getIndex():
    return '<script>s="It works! ";document.write(s);</script>'


import torch
import requests
from pprint import pprint
import numpy as np
upc_pos = torch.load('upc_pos.pkl')
ttic_pos = torch.load('ttic_pos.pkl')
def predict(pos,next_stop):
    # 最近的10个点平均
    # 返回平均的距离
    upc_dist = [(np.linalg.norm([x[0][0]-pos[0], x[0][1]-pos[1]]), x[2]) for x in upc_pos if x[1] == next_stop]
    upc_dist = sorted(upc_dist, key=lambda x:x[0])
    if len(upc_dist[:20]) == 0:
        upc_pdist,upc_time,upc_time2 = 1, 1e100, 1e100
    else:
        upc_pdist = np.array(upc_dist[:20])[:,0].mean()
        upc_time = np.array(upc_dist[:20])[:,1].min()
        upc_time2 = np.array(upc_dist[:20])[:,1].mean()
    
    ttic_dist = [(np.linalg.norm([x[0][0]-pos[0], x[0][1]-pos[1]]), x[2]) for x in ttic_pos if x[1] == next_stop]
    ttic_dist = sorted(ttic_dist, key=lambda x:x[0])
    if len(ttic_dist[:20]) == 0:
        ttic_pdist,ttic_time,ttic_time2 = 1, 1e100, 1e100
    else:
        ttic_pdist = np.array(ttic_dist[:20])[:,0].mean()
        ttic_time = np.array(ttic_dist[:20])[:,1].min()
        ttic_time2 = np.array(ttic_dist[:20])[:,1].mean()
    
    return {
        'upc_min_time' : upc_time,
        'upc_avg_time' : upc_time2,
        'upc_pdist' : upc_pdist,
        'ttic_min_time' : ttic_time,
        'ttic_avg_time' : ttic_time2,
        'ttic_pdist' : ttic_pdist
    }
def predict_all(poslist):
    upc_min = 1e100
    upc_avg = 1e100
    ttic_min = 1e100
    ttic_avg = 1e100
    upc_pdist = -1
    ttic_pdist = -1
    for pos in poslist:
        result = predict(*pos)
        if result['upc_min_time'] < upc_min:
            upc_min = result['upc_min_time']
            upc_avg = result['upc_avg_time']
            upc_pdist = result['upc_pdist']
        if result['ttic_min_time'] < ttic_min:
            ttic_min = result['ttic_min_time']
            ttic_avg = result['ttic_avg_time']
            ttic_pdist = result['ttic_pdist']
    return {
        'upc_min_time' : upc_min,
        'upc_avg_time' : upc_avg,
        'upc_pdist' : upc_pdist,
        'ttic_min_time' : ttic_min,
        'ttic_avg_time' : ttic_avg,
        'ttic_pdist' : ttic_pdist
    }   

def get_current_pos():
    ret = []
    url = 'https://feeds.transloc.com/3/vehicle_statuses?agencies=104&include_arrivals=false'
    result = requests.get(url)
    data = result.json()
    for x in data['vehicles']:
        if x['route_id'] == 8005352:
            if x['service_status'] == 'in_service':
                ret.append((x['position'], x['next_stop']))
    return ret



@app.route("/api", methods=["GET", "POST"])
def dealRequests():
    pos_now = get_current_pos()
    result = predict_all(pos_now)
    return json.dumps(result)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT)
