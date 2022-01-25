import json
import os
import sys

from flask import Flask, request, Response, render_template, make_response
from pathlib import Path

app = Flask(__name__)

# MANDATORY ztp_jsons is mounted to the container
data_dir = Path("ztp_jsons")
config_dict = {}
for json_file in data_dir.glob('*.json'):
    with open(json_file) as f:
        config_dict |= json.load(f)


def auth_ztp_host(request):
    try:
        print(request.json)
        sn = request.json['serial']

        if config_dict['serial'] != sn:
            print(f"sn: {sn} is not known")
            return 401

        return 200
    except KeyError:
        print("Did you provide the serial number in the json request body?")
        return 400
    except Exception as e:
        print(e)
        return 400


@app.route('/software', methods=['POST'])
def software():
    status = auth_ztp_host(request)
    if status != 200:
        return Response(status=status)

    sn = request.json['serial']
    try:
        version = request.json['version']
        if config_dict[sn]['bypass_software']:
            response = Response(status=204)
            response.headers['Software-Message']='Software upgrade bypass enabled'
            print(f"Software upgrade bypass enabled for host serial: {sn}")
            return response

        if config_dict[sn]['version'] == version:
            response = Response(status=204)
            response.headers['Software-Message']=f"Software already up to date. Version is {version}"
            print(f"Software upgrade not needed. version matches. host serial: {sn} sw ver: {version}")
            return response

        response = Response(status=301)
        response.content_md5 = config_dict[sn]['md5']
        response.headers['Software-Version']=config_dict[sn]['version']
        response.headers['Content-Disposition']=f"attachment; filename={config_dict[sn]['junos_file']}"
        response.headers['X-Accel-Redirect']=f"/ztp_software/{config_dict[sn]['junos_file']}"
        return response
    except KeyError:
        print("Did you provide all the required json fields?")
        return Response(status=400)
    except Exception as e:
        print(e)
        return Response(status=400)


@app.route('/config', methods=['POST'])
def config():
    status = auth_ztp_host(request)
    if status != 200:
        return Response(status=status)

    sn = request.json['serial']
    try:
        if config_dict[sn]['bypass_config']:
            response = Response(status=204)
            response.headers['Config-Message']='Configuration bypass enabled'
            print(f"Configuration bypass enabled for host serial: {sn}")
            return response

        response = Response(status=301)
        response.headers['Content-Disposition']=f"attachment; filename={config_dict[sn]['config_file']}"
        response.headers['X-Accel-Redirect']=f"/ztp_configs/{config_dict[sn]['config_file']}"
        return response
    except KeyError:
        print("Did you provide all the required json fields?")
        return Response(status=400)
    except Exception as e:
        print(e)
        return Response(status=400)


@app.route('/ztp.sh', methods=['GET'])
def send_ztp_script():
    # MANDATORY ENV vars need to be passed in to container runtime
    context = {
        'ztp_server': os.getenv('ZTP_SERVER'),
        'ztp_port': os.getenv('ZTP_PORT')
    }
    try:
        response = make_response(render_template('ztp.j2', **context))
        response.headers['Content-Disposition']=f"attachment; filename=ztp.sh"
        return response
    except Exception as e:
        print(e)
        return Response(status=400)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
