import requests
import json
import jwt
from pprint import pprint


class Api:

    # autor eggsteban
    def __init__(
        self,
        client_id="03a7b65d-0be1-4b18-b785-8d3f7c5e1961",
        client_secret="eb91a28b-ca07-4c23-aba8-833e5b4411dc",
    ):
        self.balance = 0
        self.accessToken = None
        self.transactionId = None
        self.uid = None

        self.client_id = client_id
        self.client_secret = client_secret

    def getWompyToken(self):
        data = {
            "audience": "wompi_api",
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(
            "https://id.wompi.sv/connect/token", data=data)

        # Check if the response is successful
        if response.status_code == 200:
            response = response.json()
            self.accessToken = response["access_token"]
            return response
        else:
            print("Failed to get token:", response.status_code, response.text)
            return None

    def getWompyRegions(self):

        self.getWompyToken()

        getRegions = {
            "accept": "*/*",
            "Authorization": f"Bearer {self.accessToken}",
        }
        response = requests.get(
            "https://api.wompi.sv/api/Regiones", headers=getRegions)

        if response.status_code == 200:
            regions = response.json()
            pprint(regions)
        else:
            print("Failed to get regions:", response.status_code, response.text)

    # Depricated
    def processWompyCCTransaction(
        self,
        creditCard=None,
        cvv=None,
        month=None,
        year=None,
        amountToPay=None,
        emailAddress=None,
        name=None,
    ):

        self.getWompyToken()
        print(self.accessToken)

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.accessToken}",
            "Content-Type": "application/json-patch+json",
        }
        data = {
            "tarjetaCreditoDebido": {
                "numeroTarjeta": creditCard,
                "cvv": cvv,
                "mesVencimiento": month,
                "anioVencimiento": year,
            },
            "monto": float(amountToPay),  # Ensure amount is a number
            "emailCliente": emailAddress,
            "nombreCliente": name,
            "formaPago": "PagoNormal",
        }

        # data = {
        #     "tarjetaCreditoDebido": {
        #         "numeroTarjeta": creditCard,
        #         "cvv": cvv,
        #         "mesVencimiento": month,
        #         "anioVencimiento": year,
        #     },
        #     "monto": float(amountToPay),  # Ensure amount is a number
        #     "configuracion": {
        #         "emailsNotificacion": emailAddress,
        #         # "urlWebhook": "",
        #         "telefonosNotificacion": "70505027",
        #         "notificarTransaccionCliente": True,
        #     },
        #     "urlRedirect": "https://sistemasintegradosao.com/simple-charts.html",
        #     "nombre": "Esteban T",
        #     "apellido": "Jandres T",
        #     "email": emailAddress,
        #     "ciudad": "Santa Tecla",
        #     "direccion": "Res casa verde 2 calle las rosas 19 ",
        #     "idPais": "SV",
        #     "idRegion": "SV-LI",
        #     "codigoPostal": "1611",
        #     "telefono": "70384912",
        # }

        # Debugging: Print data being sent
        print("Data sent for transaction:")
        pprint(data)

        response = requests.post(
            "https://api.wompi.sv/TransaccionCompra", headers=headers, json=data
        )

        # Debugging: Check response status and content
        print("Response status code:", response.status_code)
        print("Response content:", response.text)

        if response.status_code == 200:
            try:
                usdTransaction = response.json()
                pprint(usdTransaction)
                if usdTransaction.get("esAprobada") and usdTransaction.get("esReal"):
                    self.balance += float(usdTransaction["monto"])
                    # self.updateBalanceOnDB("processWompyCCTransaction")
                    return usdTransaction
                else:
                    print("Transaction not approved or not real")
                    return None
            except ValueError:
                print("Response is not JSON:", response.text)
                return None
        else:
            print("Failed to process transaction:",
                  response.status_code, response.text)
            return None

    def test(self):
        """
        {
            'esReal': True,
            'idTransaccion': 'adb3624a-9a3f-46a1-b82f-42c1d7b97d11',
            'monto': 1.0,
            'urlCompletarPago3Ds': 'https://pagos.wompi.sv/IntentoPago/FinalizarTransaccionApi3ds?id=adb3624a-9a3f-46a1-b82f-42c1d7b97d11'
        }

        """

        self.getWompyToken()
        headers = {
            "accept": "text/plain",
            "Authorization": f"Bearer {self.accessToken}",
            "Content-Type": "application/json-patch+json",
        }

        data = {
            "apellido": "jandres",
            "ciudad": "Santa Tecla",
            "codigoPostal": "1611",
            "configuracion": {
                "emailsNotificacion": "esteban.g.jandres@gmail.com",
                "notificarTransaccionCliente": True,
                "telefonosNotificacion": "70384912",
            },
            "direccion": "Res casa verde 2 calle las rosas 19 ",
            "email": "esteban.g.jandres@gmail.com",
            "idPais": "SV",
            "idRegion": "SV-LI",
            "monto": 1,
            "nombre": "Esteban Gutierrez",
            "tarjetaCreditoDebido": {
                "anioVencimiento": "2028",
                "cvv": "741",
                "mesVencimiento": "05",
                "numeroTarjeta": "5230450606095400",
            },
            "telefono": "70384912",
            "urlRedirect": "https://sistemasintegradosao.com/simple-charts.html",
        }

        response = requests.post(
            "https://api.wompi.sv/TransaccionCompra/3Ds",
            headers=headers,
            data=json.dumps(data),
        )
        response = response.json()
        pprint(response)
        self.transactionId = response["idTransaccion"]
        return response

    def t(
        self,
        data={
            "name": "Esteban",
            "phone": "5037038",
            "address": "Res nta Tecla",
            "email": "este",
            "year": "228",
            "cvv": "71",
            "month": "05",
            "card": "5295469",  # Example credit card number (test card)
        },
    ):
        """
        response 200
        {
            'esReal': True,
            'idTransaccion': 'adb3624a-9a3f-46a1-b82f-42c1d7b97d11',
            'monto': 1.0,
            'urlCompletarPago3Ds': 'https://pagos.wompi.sv/IntentoPago/FinalizarTransaccionApi3ds?id=adb3624a-9a3f-46a1-b82f-42c1d7b97d11'
        }

        response 400

         {
            'mensajes': ['El número de tarjeta no es válido'],
            'servicioError': 'TransaccionCompraController',
            'subTipoError': None
         }

        """

        self.getWompyToken()
        headers = {
            "accept": "text/plain",
            "Authorization": f"Bearer {self.accessToken}",
            "Content-Type": "application/json-patch+json",
        }

        name = data["name"].split(" ")
        # print(f"3333333333333333333333333 {name}")

        if "phone" not in data:
            data["phone"] = "+18083216547"

        json_request = {
            "nombre": name[0],
            "apellido": name[1] if len(name) == 2 else name[2],
            "telefono": data["phone"],
            "ciudad": data["address"],
            "codigoPostal": "1611",
            "direccion": data["address"],
            "email": data["email"],
            "idPais": "SV",
            "idRegion": "SV-LI",
            "monto": data["amount"],
            "tarjetaCreditoDebido": {
                "anioVencimiento": data["year"],
                "cvv": data["cvv"],
                "mesVencimiento": data["month"],
                "numeroTarjeta": data["card"],
            },
            "configuracion": {
                "emailsNotificacion": "esteban.g.jandres@gmail.com",
                "notificarTransaccionCliente": True,
                "telefonosNotificacion": "70384912",
            },
            "urlRedirect": "https://sistemasintegradosao.com/simple-charts.html",
        }

        # pprint(json_request)

        response = requests.post(
            "https://api.wompi.sv/TransaccionCompra/3Ds",
            headers=headers,
            data=json.dumps(json_request),
        )
        return response.json()

    def chekOnLinkPayment(self, id):
        pass

    def checkTransactionStatus(self, id):
        """

        Returns:_type_: {'codigoAutorizacion': '102448',
        'datosAdicionales': {'Apellidos': 'jandres',
                            'CantidadCompra': '1',
                            'Celular': '70384912',
                            'CodigoPais': 'SV',
                            'CodigoRegion': 'SV-LI',
                            'Direccion': 'Res casa verde 2 calle las rosas 19 ',
                            'EMail': 'esteban.g.jandres@gmail.com',
                            'Nombre': 'Esteban Gutierrez',
                            'NombrePais': 'El Salvador',
                            'NombreRegion': 'La Libertad',
                            'UrlRedirect3dsCliente': 'https://sistemasintegradosao.com/simple-charts.html',
                            'UrlRedirectTransaccion3dsApi': 'https://pagos.wompi.sv/IntentoPago/FinalizarTransaccionApi3ds?id=adb3624a-9a3f-46a1-b82f-42c1d7b97d11'},
        'datosBitcoin': None,
        'esAprobada': True,
        'esReal': True,
        'fechaTransaccion': '2024-08-26T14:26:49.0336649-06:00',
        'formaPago': 'PagoNormal',
        'idTransaccion': 'adb3624a-9a3f-46a1-b82f-42c1d7b97d11',
        'mensaje': 'AUTORIZADO',
        'monto': 1.0,
        'montoOriginal': None,
        'resultadoTransaccion': 'ExitosaAprobada'}

        """

        self.getWompyToken()

        # print(self.accessToken)
        # print(id)

        headers = {
            "accept": "text/plain",
            "Authorization": f"Bearer {self.accessToken}",
        }
        if id is not None:

            response = requests.get(
                f"https://api.wompi.sv/TransaccionCompra/{id}",
                headers=headers,
            )
            return response.json()

    def encode_data(self, data_to_encrypt):
        private_key = b"-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQBs3YkuQIbBkk7l82JbmqxV8vb+zEJlS7LyzLhOWrKcgBVelPwt\nkctxxxPbi2JHftSBXJRsJ/zfp+LjixDBNmCIPdBwVQUFFh3YWPB/N6vkHC5sfNX6\nHc3LypVcQavp8UFoCOTj/VPdVW5xqQBul2/vnxxHl8GxiFWn3xsj0eroDPlUb7Zw\nATkHp2+QvjSTZFfy+3IOrPsdqcff5noyIt0axaJ+g4+4OZL1ysU6xAaIk/vsihYa\nCdN3c+ra4XORjwKEC1SiRXueDkkcyQS2XuILBHo2iYaE7QxRQf4JAB0z3DzJtOtj\nygKScrwarXSULrSFGaU6MwxfdMiDDd0FD/HnAgMBAAECggEACGD0ke69cGCGWgRl\naY95/BN7Fxk5cvpkh3NiLAWnAYyKGIF29zrlYZhk2tzbb40/ZcVuVvSs7bnKKKEn\nZPd+bn3zcPHaNQ4CtggCWog6XpAcspTZEysAD9NDs5oKVTMQSaWFmFaDAeH1YiIT\num9FWjfwwUHY0oUfso/lUthxL/LVNEk/AIVvuIhC4jECdsFR+FU04wOQBZRMix1R\nKoHbOnIJDlThmVFxk7LZhxuVHTmcfgSwcIhEQVxjjsyTFGJhuqwkdUo5ZN28/Nbc\ntUAGl9Ple4y8Q7irG5HoTAs2aH1EiAUK9soe7bx1v4xxBTdzxLFlIJcuyqKhPUaI\ni9NH4QKBgQDVWfxdM/d06TTbQPruEO6cRE30jGHX+IQ85fn7HrVySKJk/b2/jRQ0\nSaAFLFwypfA08lUVG58AaOT/NzTguT43nWZ6AylKPjeWajaP3Ap6cffbdYpedkwq\nPM9MyXeVDd2ZYt+8K1bdcQQ+3wEV7P/gZYKt41z9AunbS8dNoRX44wKBgQCCoJgh\nUO0g/8sfdE+GRI0+8rqfzpqQguwvcmtdlmu0f9piOtZ2uyGRkijcYPnIeb8Yz4Ol\n+1YTvE4cz1C3VrgE6Mg48zl+XNZmo8J9+5YwYrflojqmGvcFMGmQQs5ycOxQtbmg\nTrno18TLzIOI/6w9rtuyAsXZrHU15kjnYPCmLQKBgQCaI20EGStKt8GMNiIUJP9+\nvopjh5iY498F8FDucH0+l+Nbe0a/QTm7nQWTNz1VCjXEyt9VZKM3NJFdIZF+Wdbt\nbzY+KFKIZPLcJNhOjvazB+u+Delt3aGhUlWicFuIwH+89YYW+GjFi4U5tvudz5/9\nitkisATadmRmHxVarGqnaQKBgG+GTvw6zImc+j3bnr3Cr1jsAXvI99uje6SyqonX\nkBMmCTxOgaYS9IEFaY9l2DxZ/VZgbUR7xizJW2NreL1e83N1juRYfGCvQHmXHMlU\n0BB1aA5NKIeChB3RDH+XGg1I7emmjVoZfM4X0bQx4qdHqjVrobRke6jxfYzMFLg+\n4pbtAoGBAMyZ30w3CEUMImoMKNhV8g8ZUO4mur4QHpwDsU8bkP/KdkRIkUGXjWJ2\n512oDCUNtwVbib9bUGhqie/0NurQn3eamwgR/sx88n6T6aG+nQfPgDNHAc6N5Mzb\nMTf+j68ImBnljIKtu5gPjE+k2P3PxAlGB19cbynFo3R4MgPw3bFJ\n-----END RSA PRIVATE KEY-----\n"
        return jwt.encode(data_to_encrypt, private_key, algorithm="RS256")

    def decode_data(self, encoded):
        public_key = b"-----BEGIN PUBLIC KEY-----\nMIIBITANBgkqhkiG9w0BAQEFAAOCAQ4AMIIBCQKCAQBs3YkuQIbBkk7l82JbmqxV\n8vb+zEJlS7LyzLhOWrKcgBVelPwtkctxxxPbi2JHftSBXJRsJ/zfp+LjixDBNmCI\nPdBwVQUFFh3YWPB/N6vkHC5sfNX6Hc3LypVcQavp8UFoCOTj/VPdVW5xqQBul2/v\nnxxHl8GxiFWn3xsj0eroDPlUb7ZwATkHp2+QvjSTZFfy+3IOrPsdqcff5noyIt0a\nxaJ+g4+4OZL1ysU6xAaIk/vsihYaCdN3c+ra4XORjwKEC1SiRXueDkkcyQS2XuIL\nBHo2iYaE7QxRQf4JAB0z3DzJtOtjygKScrwarXSULrSFGaU6MwxfdMiDDd0FD/Hn\nAgMBAAE=\n-----END PUBLIC KEY-----\n"
        return jwt.decode(encoded, public_key, algorithms=["RS256"])


def process_cc(
    client_id="03a7b65d-0be1-4b18-b785-8d3f7c5e1961",
    client_secret="eb91a28b-ca07-4c23-aba8-833e5b4411dc",
    data={},
):
    api = Api(client_id, client_secret)
    return api.t(data)


def get_regiones(
    client_id="03a7b65d-0be1-4b18-b785-8d3f7c5e1961",
    client_secret="eb91a28b-ca07-4c23-aba8-833e5b4411dc",
):
    api = Api(client_id, client_secret)
    return api.getWompyRegions()


def get_transacition_status(
    id,
    client_id="03a7b65d-0be1-4b18-b785-8d3f7c5e1961",
    client_secret="eb91a28b-ca07-4c23-aba8-833e5b4411dc",
):
    return Api(client_id, client_secret).checkTransactionStatus(id)


def encode(data_to_save):
    return Api().encode_data(data_to_save)


if __name__ == "__main__":

    id = "5727337f-ae14-41ce-80b6-5f9d8985a114"
    # response = process_cc()
    # pprint(response.json())
    # pprint(get_transacition_status(id))
    # pprint(get_regiones())
    # pprint(process_cc())

    # Example usage code decode
    # api = Api()

    # e = api.encode_data({"name": "estebas"})
    # print(api.decode_data(e))
