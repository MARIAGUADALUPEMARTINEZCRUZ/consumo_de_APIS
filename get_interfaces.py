import json
import requests
from flask import Flask, render_template, request, redirect, url_for, flash

requests.packages.urllib3.disable_warnings()

app = Flask(__name__)
app.secret_key = 'supersecretkey'

api_url = "https://192.168.56.101/restconf/"
headers = {
    "Accept": "application/yang-data+json",
    "Content-type": "application/yang-data+json"
}
basicauth = ("cisco", "cisco123!")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/interfaces')
def get_interfaces():
    module = "data/ietf-interfaces:interfaces"
    resp = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)
    data_json = resp.json()
    interfaces = []

    if resp.status_code == 200:
        for interface in data_json["ietf-interfaces:interfaces"]["interface"]:
            interfaces.append({
                'name': interface['name'],
                'ip':['ip'],
                'description': interface.get('description', 'N/A'),
                'enabled': interface['enabled']
            })
    return render_template('interfaces.html', interfaces=interfaces)


@app.route('/banner')
def get_banner():
    module = "data/Cisco-IOS-XE-native:native/banner/motd"
    resp = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)
    banner = ""

    if resp.status_code == 200:
        banner = resp.json().get("Cisco-IOS-XE-native:motd", {}).get("banner", "")

    return render_template('banner.html', banner=banner)


@app.route('/agregar', methods=['GET', 'POST'])
def post_loopback():
    if request.method == 'POST':
        loopback_name = request.form['nombre']
        ip = request.form['ip']
        netmask = request.form['mascara']
        descripcion = request.form['descripción']

        dloopback = {
            "ietf-interfaces:interface": {
                "name": loopback_name,
                "description": descripcion,
                "type": "iana-if-type:softwareLoopback",
                "enabled": True,
                "ietf-ip:ipv4": {
                    "address": [
                        {
                            "ip": ip,
                            "netmask": netmask
                        }
                    ]
                }
            }
        }

        module = "data/ietf-interfaces:interfaces"
        resp = requests.post(f'{api_url}{module}', auth=basicauth, headers=headers, data=json.dumps(dloopback), verify=False)

        if resp.status_code == 201:
            flash(f"Loopback: {loopback_name} agregado exitosamente!", "success")
            return json.dumps({'status': 'success', 'message': f"Loopback: {loopback_name} agregado exitosamente!"}), 201
        else:
            flash(f"Error al agregar Loopback {loopback_name}", "danger")
            return json.dumps(
                {'status': 'error', 'message': f"Error al agregar Loopback: {loopback_name}"}), resp.status_code

    return render_template('agregar.html')


@app.route('/eliminar', methods=['GET','POST'])
def del_loopback():
    if request.method == 'POST':
        loopback_name = request.form['nombre']

        module = f"data/ietf-interfaces:interfaces/interface={loopback_name}"
        resp = requests.delete(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)

        if resp.status_code == 204:
            flash(f"Loopback {loopback_name} eliminado exitosamente!", "success")
            return json.dumps({'status': 'success', 'message': f"Loopback {loopback_name} eliminado exitosamente!"}), 204
        else:
            flash(f"Error al eliminar Loopback {loopback_name}", "danger")
            return json.dumps(
                {'status': 'error', 'message': f"Error al eliminar Loopback {loopback_name}"}), resp.status_code

    return render_template('eliminar.html')  # Renderiza la plantilla 'eliminar.html'

if __name__ == '__main__':
    app.run(debug=True)
