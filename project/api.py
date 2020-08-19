"""
API permettant de récupérer les informations de la méthode middleware de Misyl
Le but est de créer une page suivi de colis, qui viendra attaquer cette API
Cette API trace le colis et donne les informations aux consommateurs (rendez-vous, informations relais...)
"""

import json
import requests
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__, static_folder='static')  # Instancie une nouvelle application

""" Cette classe permet d'aller attaquer l'API middleware contenant les informations clients"""


class ApiKnow:
    def __init__(self, trackingNumber):
        self.trackingNumber = str(trackingNumber)

        # Permet d'aller taper l'API api/chatbot/known?trackingNumber={trackingNumber} permettant de vérifier le
        # numéro de suivi du consommateur

        url = "https://middlewarepreprod.misyl.net/api/chatbot/known?trackingNumber=" + trackingNumber

        payload = {}
        headers = {}

        contentKnow = requests.request("GET", url, headers=headers, data=payload)

        fileKnow = contentKnow.json()

        with open('data/know.json', 'w') as f:
            json.dump(fileKnow, f)


class ApiKolis:
    def __init__(self, trackingNumber, customerEmail):
        self.trackingNumber = str(trackingNumber)
        self.customerEmail = str(customerEmail)
        # Permet d'attaquer l'API api/chatbot/colis?trackingNumber={trackingNumber}&email={customerEmail} permettant
        # de récuperer les informations du consommateur

        url = "https://middlewarepreprod.misyl.net/api/chatbot/colis?trackingNumber=" + trackingNumber + "&email=" + customerEmail

        payload = {}
        headers = {}

        contentKolis = requests.request("GET", url, headers=headers, data=payload)

        fileKolis = contentKolis.json()

        with open('data/kolis.json', 'w') as fout:
            json.dump(fileKolis, fout)


""" Première route de l'API suivi de colis"""


@app.route('/api/tracking', methods=['GET', 'POST'])
# Cette première fonction va permettre de vérifier si le client est connu grâce à son numéro de suivi, puis de récupérer ses informations

def verifiedClient():
    if request.method == 'GET':
        return render_template("tracking.html")

    if request.method == 'POST':

        trackingNumber = str(request.form.get("TrackingNumber"))  # Numéro de suivi du consommateur

        ApiKnow(trackingNumber)

        know_file = json.loads(open('data/know.json', 'rb').read())

        IsColisinDatabase = know_file['data']['isColisInDatabase']

        if IsColisinDatabase == True:
            return render_template("tracking.html", user_tracking=trackingNumber) and redirect(
                url_for('dataClient', TrackingNumber=trackingNumber))

        else:
            return render_template("tracking.html",
                                   tracking_verified="Vous n'êtes pas dans notre base de donné, désolé")


""" Nouvelle route kolis/{TrackingNumber} qui va gérer les différents status et vérifier si l'email rentré est correct"""


@app.route('/api/tracking/<TrackingNumber>', methods=['GET', 'POST'])
def dataClient(TrackingNumber):
    if request.method == "GET":
        return render_template("data.html",
                               tracking_verified="Vous êtes dans notre base de données! Rentrer votre adresse mail "
                                                 "afin d'avoir plus d'infromation sur votre colis.")

    if request.method == 'POST':
        customerEmail = str(request.form.get('EmailUser'))
        ApiKolis(TrackingNumber, customerEmail)

        kolis_file = json.loads(open('data/kolis.json', 'rb').read())

        # Test si l'email de l'utilisateur est connu
        if kolis_file['status'] == 500:
            return render_template("data.html", error_mail=kolis_file['data']['message'])

        elif kolis_file['status'] == 204:
            return render_template("data.html", error_data=kolis_file['data']['message'])

        elif kolis_file['status'] == 200:

            # Récupère toutes les informations nécessaires sur le colis du consommateur
            status = int(kolis_file['data']['data']['status'])
            meetingLink = kolis_file['data']['data']['meetingLink']
            meetingDateTime = kolis_file['data']['data']['meetingDatetime']
            productWidth = kolis_file['data']['data']['productWidth']
            productHeight = kolis_file['data']['data']['productHeight']
            productWeight = kolis_file['data']['data']['productWeight']
            relayMaps = kolis_file['data']['data']['relayMaps']
            productLength = kolis_file['data']['data']['productLength']
            productVolume = kolis_file['data']['data']['productVolume']
            relayAddress = kolis_file['data']['data']['relayAddress']
            relayName = kolis_file['data']['data']['relayName']
            productDescription = kolis_file['data']['data']['productDescription']

            # Colis en attente de réception
            if status == 1:
                return render_template("data.html", wait_reception="Votre colis est en cours de livraison!",
                                       relayAddress=relayAddress, relayName=relayName, relayMaps=relayMaps,
                                       resultmeeting="Vous pourrez prendre rendez-vous une fois le colis réceptionné "
                                                     "par le relais.",
                                       status=kolis_file['status'],
                                       image_waitreception=url_for('static', filename='Wait_reception.png'))


            # Colis réceptionné mais pas de rendez-vous
            elif status == 2:
                return render_template("data.html",
                                       received="Votre colis est arrivé! Pensez à prendre un rendez-vous afin de "
                                                "récupérer votre colis.",
                                       result_meeting=meetingLink, relayAddress=relayAddress,
                                       relayName=relayName, relayMaps=relayMaps,
                                       status=kolis_file['status'],
                                       image_received=url_for('static', filename='received.png'))

            # Colis récpetionné et rdv fixé
            elif status == 3:
                return render_template("data.html",
                                       meeting_fixed="Votre colis est arrivé et vous avez un rendez-vous! Vous pouvez "
                                                     "changer celui ci en cliquant sur le lien proposé ci dessous.",
                                       result_meeting=meetingDateTime,
                                       change_meeting="Vous pouvez changer de rendez vous en cliquand sur le lien "
                                                      "suvant: " + meetingLink,
                                       relayAddress=relayAddress,
                                       relayName=relayName, relayMaps=relayMaps, status=kolis_file['status'],
                                       image_meetingfixed=url_for('static', filename='meeting_fixed.png'))

            # Colis déjà remis au client
            elif status == 4:
                return render_template("data.html", delivered_to_client="Votre colis vous a été remis.",
                                       status=kolis_file['status'],
                                       relayAddress=relayAddress,
                                       relayName=relayName, relayMaps=relayMaps,
                                       image_delivered=url_for('static', filename='delivered.png'))

            # Colis annulé
            elif status > 4:
                return render_template("data.html",
                                       order_canceled="Votre commande a été annnulé. Merci de contacter le "
                                                      "support", relayAddress=relayAddress,
                                       relayName=relayName, relayMaps=relayMaps, status=kolis_file['status'],
                                       image_canceled=url_for('static', filename='canceled.png'))

    else:
        return render_template("data.html", error_mail="Désolé, votre email n'est pas correct. Merci de la rentrer à "
                                                       "nouveau.")


if __name__ == '__main__':
    app.run(debug=True)
