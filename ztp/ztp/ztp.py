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


def get_client_ip(request):
    status = None
    client_ip = request.headers['X-Forwarded-For']
    if not client_ip:
        print("Client IP could not be determined.")
        status = 400
    if client_ip not in config_dict.keys():
        print(f"ip: {client_ip} is not an authorized ztp host")
        status = 401
    return client_ip, status


def auth_ztp_host(request):
    client_ip, err_resp = get_client_ip(request)
    if err_resp:
        return err_resp

    try:
        print(request.json)
        sn = request.json['serial']
        mac = request.json['mac']
        hostname = request.json['hostname']

        if config_dict[client_ip]['hostname'] != hostname:
            print(f"hostname: {hostname} does not match expected value for ip {client_ip}")
            return 401

        if config_dict[client_ip]['serial'] != sn:
            print(f"sn: {sn} does not match expected value for ip {client_ip}")
            return 401

        if config_dict[client_ip]['mac'] != mac:
            print(f"mac: {mac} does not match expected value for ip {client_ip}")
            return 401

        return 200
    except KeyError:
        print("Did you provide all the required json fields?")
        return 400
    except Exception as e:
        print(e)
        return 400


@app.route('/software', methods=['POST'])
def software():
    status = auth_ztp_host(request)
    if status != 200:
        return Response(status=status)

    client_ip = request.headers['X-Forwarded-For']
    try:
        version = request.json['version']
        if config_dict[client_ip]['bypass_software']:
            response = Response(status=204)
            response.headers['Software-Message']='Software upgrade bypass enabled'
            print(f"Software upgrade bypass enabled for host: {client_ip}")
            return response

        if config_dict[client_ip]['version'] == version:
            response = Response(status=204)
            response.headers['Software-Message']=f"Software already up to date. Version is {version}"
            print(f"Software upgrade not needed. version matches. host: {client_ip} sw ver: {version}")
            return response

        response = Response(status=301)
        response.content_md5 = config_dict[client_ip]['md5']
        response.headers['Software-Version']=config_dict[client_ip]['version']
        response.headers['Content-Disposition']=f"attachment; filename={config_dict[client_ip]['junos_file']}"
        response.headers['X-Accel-Redirect']=f"/ztp_software/{config_dict[client_ip]['junos_file']}"
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

    client_ip = request.headers['X-Forwarded-For']
    try:
        if config_dict[client_ip]['bypass_config']:
            response = Response(status=204)
            response.headers['Config-Message']='Configuration bypass enabled'
            print(f"Configuration bypass enabled for host: {client_ip}")
            return response

        response = Response(status=301)
        response.headers['Content-Disposition']=f"attachment; filename={config_dict[client_ip]['config_file']}"
        response.headers['X-Accel-Redirect']=f"/ztp_configs/{config_dict[client_ip]['config_file']}"
        return response
    except KeyError:
        print("Did you provide all the required json fields?")
        return Response(status=400)
    except Exception as e:
        print(e)
        return Response(status=400)


@app.route('/ztp.sh', methods=['GET'])
def send_ztp_script():
    client_ip, err_resp = get_client_ip(request)
    if err_resp:
        return Response(status=err_resp)
    try:
        hostname = config_dict[client_ip]['hostname']
    except KeyError:
        print(f"missing hostname in config data dictionary for ip {client_ip}")
        return Response(status=400)

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
