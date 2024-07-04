import json
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

requests.packages.urllib3.disable_warnings()

app = Flask(__name__)
app.secret_key = 'supersecretkey'

api_url = "https://192.168.56.101/restconf/"
headers = {
    "Accept": "application/yang-data+json",
    "Content-type": "application/yang-data+json"
}
basicauth = ("cisco", "cisco123!")
original_hostname = None  # Variable global para almacenar el hostname original

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
            ip_addresses = interface.get('ietf-ip:ipv4', {}).get('address', [])
            ip = ip_addresses[0]['ip'] if ip_addresses else 'N/A'
            netmask = ip_addresses[0]['netmask'] if ip_addresses else 'N/A'
            interfaces.append({
                'name': interface['name'],
                'ip': ip,
                'netmask': netmask,
                'description': interface.get('description', 'N/A'),
                'enabled': interface['enabled']
            })
    return render_template('interfaces.html', interfaces=interfaces)


@app.route('/hostname', methods=['GET', 'POST'])
def configure_hostname():
    message = None
    current_hostname = None
    global original_hostname

    # Obtener el hostname actual
    try:
        module = "data/Cisco-IOS-XE-native:native/hostname"
        resp = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)

        if resp.status_code == 200:
            current_hostname = resp.json().get('Cisco-IOS-XE-native:hostname', 'Hostname no disponible')
            # Guardar el nombre actual como original si aún no se ha guardado
            if original_hostname is None:
                original_hostname = current_hostname
        else:
            current_hostname = f"Error al obtener el hostname: {resp.status_code} - {resp.text}"

    except requests.exceptions.RequestException as e:
        current_hostname = f"Error de conexión: {str(e)}"

    if request.method == 'POST':
        if 'update' in request.form:
            new_hostname = request.form['hostname']
            data = {
                "Cisco-IOS-XE-native:hostname": new_hostname
            }

            try:
                resp = requests.put(f'{api_url}{module}', auth=basicauth, headers=headers, json=data, verify=False)

                if resp.status_code == 200 or resp.status_code == 204:
                    message = f"Hostname actualizado con éxito a {new_hostname}"
                else:
                    message = f"Error al actualizar el hostname: {resp.status_code} - {resp.text}"

            except requests.exceptions.RequestException as e:
                message = f"Error de conexión: {str(e)}"


        elif 'delete' in request.form:
            try:
                # Restaurar el hostname anterior
                data = {
                    "Cisco-IOS-XE-native:hostname": original_hostname
                }
                resp = requests.put(f'{api_url}{module}', auth=basicauth, headers=headers, json=data, verify=False)

                if resp.status_code == 200 or resp.status_code == 204:
                    message = f"Hostname eliminado con éxito ({original_hostname})"
                    current_hostname = original_hostname  # Restaurar el nombre actual al original
                else:
                    message = f"Error al eliminar el hostname: {resp.status_code} - {resp.text}"

            except requests.exceptions.RequestException as e:
                message = f"Error de conexión: {str(e)}"

    return render_template('hostname.html', message=message, current_hostname=current_hostname)


@app.route('/banner')
def get_banner():
    module = "data/Cisco-IOS-XE-native:native/banner/motd"
    resp = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)
    banner = ""

    if resp.status_code == 200:
        banner = resp.json().get("Cisco-IOS-XE-native:motd", {}).get("banner", "")
    else:
        print(f"Error: Received status code {resp.status_code}")
        print(f"Response: {resp.text}")

    if not banner:
        banner = "No se encontró ningún banner."

    return render_template('banner.html', banner=banner)

@app.route('/banner', methods=['GET', 'POST'])
def manage_banner():
    if request.method == 'POST':
        new_banner_text = request.form['new_banner']
        module = "data/Cisco-IOS-XE-native:native/banner/motd"
        data = {
            "Cisco-IOS-XE-native:motd": {
                "banner": new_banner_text
            }
        }

        try:
            resp = requests.put(f'{api_url}{module}', auth=basicauth, headers=headers, json=data, verify=False)

            if resp.status_code == 200 or resp.status_code == 204:
                message = "Banner actualizado con éxito"
            else:
                message = f"Error al actualizar el banner: {resp.status_code} - {resp.text}"
        
        except requests.exceptions.RequestException as e:
            message = f"Error de conexión: {str(e)}"

        return redirect(url_for('manage_banner', message=message))
    
    elif request.method == 'GET':
        module = "data/Cisco-IOS-XE-native:native/banner/motd"
        resp = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)
        banner = ""

        if resp.status_code == 200:
            banner = resp.json().get("Cisco-IOS-XE-native:motd", {}).get("banner", "")
        else:
            print(f"Error: Received status code {resp.status_code}")
            print(f"Response: {resp.text}")

        if not banner:
            banner = "No se encontró ningún banner."

        message = request.args.get('message')

        return render_template('banner.html', banner=banner, message=message)


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
            return jsonify({'status': 'success', 'message': f"Loopback: {loopback_name} agregado exitosamente!"}), 201
        else:
            flash(f"Error al agregar Loopback {loopback_name}", "danger")
            return jsonify({'status': 'error', 'message': f"Error al agregar Loopback: {loopback_name}"}), resp.status_code

    return render_template('agregar.html')


@app.route('/modificar', methods=['GET', 'POST'])
def modify_interface():
    if request.method == 'POST':
        interface_name = request.form['nombre']
        new_ip = request.form['ip']
        new_netmask = request.form['mascara']
        new_description = request.form['descripción']

        module = f"data/ietf-interfaces:interfaces/interface={interface_name}"
        resp_get = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)

        if resp_get.status_code == 200:
            interface_data = resp_get.json().get("ietf-interfaces:interface", {})
            interface_data['description'] = new_description

            # Modificar la dirección IP si está presente en la interfaz
            if 'ietf-ip:ipv4' in interface_data:
                if 'address' in interface_data['ietf-ip:ipv4'] and len(interface_data['ietf-ip:ipv4']['address']) > 0:
                    interface_data['ietf-ip:ipv4']['address'][0]['ip'] = new_ip
                    interface_data['ietf-ip:ipv4']['address'][0]['netmask'] = new_netmask
                else:
                    interface_data['ietf-ip:ipv4']['address'] = [{'ip': new_ip, 'netmask': new_netmask}]
            else:
                interface_data['ietf-ip:ipv4'] = {'address': [{'ip': new_ip, 'netmask': new_netmask}]}

            resp_put = requests.put(f'{api_url}{module}', auth=basicauth, headers=headers,
                                    data=json.dumps({"ietf-interfaces:interface": interface_data}),
                                    verify=False)

            if resp_put.status_code == 200:
                flash(f"Interfaz {interface_name} modificada exitosamente!", "success")
                return jsonify({'status': 'success', 'message': f"Interfaz {interface_name} modificada exitosamente!"}), 200
            else:
                flash(f"Error al modificar Interfaz {interface_name}", "danger")
                print(f"Error al modificar: {resp_put.status_code} - {resp_put.text}")
                return jsonify({'status': 'error', 'message': f"Error al modificar Interfaz {interface_name}"}), resp_put.status_code
        else:
            flash(f"Interfaz {interface_name} no encontrada", "danger")
            print(f"Error al obtener interfaz: {resp_get.status_code} - {resp_get.text}")
            return jsonify({'status': 'error', 'message': f"Interfaz {interface_name} no encontrada"}), resp_get.status_code

    return render_template('modificar.html')

@app.route('/eliminar', methods=['GET', 'POST'])
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

 
    return render_template('eliminar.html')

    #return redirect(url_for('eliminar.html'))

@app.route('/dhcp', methods=['GET'])
def show_dhcp_form():
    return render_template('dhcp.html')

@app.route('/dhcp-config', methods=['GET', 'POST'])
def configure_dhcp():
    message = None
    success = False

    if request.method == 'POST':
        # Obtener datos del formulario
        dhcp_name = request.form['dhcp_name']
        ip_range = request.form['dhcp_ip_range']
        subnet_mask = request.form['dhcp_subnet_mask']
        default_router = request.form['dhcp_default_router']
        dns = request.form['dhcp_dns']

        # Construir el JSON para la configuración DHCP
        data = {
            "Cisco-IOS-XE-native:dhcp": {
                "name": dhcp_name,
                "ip": {
                    "address": ip_range,
                    "mask": subnet_mask,
                    "default-router": default_router,
                    "dns-server": dns
                }
            }
        }

        # URL del módulo de configuración DHCP en tu API
        module = "data/Cisco-IOS-XE-native:native/ip/dhcp"

        try:
            # Realizar la solicitud PUT al dispositivo con los datos JSON
            resp = requests.put(f'{api_url}/{module}', auth=basicauth, headers=headers, json=data, verify=False)

            # Verificar la respuesta del servidor
            if resp.status_code == 200 or resp.status_code == 204:
                message = "Configuración DHCP aplicada correctamente"
                success = True
            else:
                message = f"Error al aplicar la configuración DHCP: {resp.status_code} - {resp.text}"

        except Exception as e:
            message = f"Error al conectar con la API: {str(e)}"

    return render_template('dhcp.html', message=message, success=success)

if __name__ == '__main__':
    app.run(port=5001)

