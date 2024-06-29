import json
import requests

requests.packages.urllib3.disable_warnings()


def get_interfaces():
    module = "data/ietf-interfaces:interfaces"
    resp = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)
    print(json.dumps(resp.json(), indent=4))
    data_json = resp.json()
    if resp.status_code == 200:
        for key, valor in data_json.items():
            print(f'Nombre de la interface: {valor["interface"][1]["name"]}')
            print(f'Descripción de la interface: {valor["interface"][1]["description"]}')
            print(f'Status de la interface: {valor["interface"][1]["enabled"]}')
    else:
        print(f'Error al realizar la consulta del modulo {module}')


def get_restconf_native():
    module = "data/Cisco-IOS-XE-native:native"
    resp = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)
    if resp.status_code == 200:
        print(json.dumps(resp.json(), indent=4))
    else:
        print(f"Error al consumir la API para el modulo {module}")


def banner_motd():
    module = "data/Cisco-IOS-XE-native:native/banner/motd"
    resp = requests.get(f'{api_url}{module}', auth=basicauth, headers=headers, verify=False)
    if resp.status_code == 200:
        print(json.dumps(resp.json(), indent=4))
    else:
        print(f"Error al consumir la API para el modulo {module}")


def put_banner():
    banner = {
        "Cisco-IOS-XE-native:motd": {
            "banner": "#Solo tienen permiso los priviligiados"
        }
    }

    module = "data/Cisco-IOS-XE-native:native/banner/motd"
    resp = requests.put(f'{api_url}{module}', data=json.dumps(banner), auth=basicauth, headers=headers, verify=False)
    print(resp.status_code)
    if resp.status_code == 204:
        print("Actualización exitosa")
    else:
        print(f"Error, no se puede realizar la actualización al modulo{module}")


def post_loopback():
    dloopback = json.dumps({
        "ietf-interfaces:interface": {
            "name": "Loopback100",
            "description": "Configured by RESTCONF",
            "type": "iana-if-type:softwareLoopback",
            "enabled": True,
            "ietf-ip:ipv4": {
                "address": [
                    {
                        "ip": "172.16.100.1",
                        "netmask": "255.255.255.0"
                    }
                ]
            }
        }
    })

    module = "data/ietf-interfaces:interfaces"
    resp = requests.post(f'{api_url}{module}', auth=basicauth, headers=headers, data=dloopback, verify=False)
    if resp.status_code == 201:
        print(f"Se insertó correctamente {dloopback}")
    else:
        print(f"Error al insertar elemento al módulo{module}")


def del_loopback():
    module = "data/ietf-interfaces:interfaces/interface=Loopback100"
    dloopback = {}
    resp = requests.delete(f'{api_url}{module}', auth=basicauth, headers=headers, data=dloopback, verify=False)
    if resp.status_code == 204:
        print(f"Se eliminó correctamente el elemento")
        get_interfaces()
    else:
        print(f"Error al eliminar el elemento del módulo{module}")


if __name__ == '__main__':
    # module:operations, data
    api_url = "https://192.168.56.101/restconf/"
    headers = {"Accept": "application/yang-data+json",
               "Content-type": "application/yang-data+json"
               }
    basicauth = ("cisco", "cisco123!")

    get_interfaces()
    #get_restconf_native()
    #banner_motd()
    #put_banner()
    #post_loopback()
    #del_loopback()

    # Diseñar interfaces gráficas amigables que pemitan hacer estaa pues este comsumo de las apis,
    # agregar dos elementos diferentes de IOS-XE-native en HTML o en programa de escritorio