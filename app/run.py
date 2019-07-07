import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from os import getenv, environ
from dotenv import load_dotenv
from bs4 import BeautifulSoup


def get_files_to_follow() -> list:
    """
    Obtener todos los ficheros de seguimimento para realizar consultas de scraping
    :return: <list> Se devuelve una lista de objetos PATH conteniendo la ruta absoluta de los ficheros
    """
    links = Path(getenv('DIR_ROOT_APP')) / getenv('DIR_LINKS')
    return list(links.glob('*'))


def load_json(file: str) -> dict:
    """
    Deserializar un objetos JSON en un diccionario python
    :param file: <str> Pathh absoluto del fichero que contiene el JSON
    :return: <dict> El JSON contenido en el fichero lo devolvemos com un diccionario
    """

    with open(file, "r") as read_file:
        return json.load(read_file)


def searching() -> None:
    """
    Metodo para realizar la busqueda de precio en las url's solicitadas
    :return: None
    """
    for file in get_files_to_follow():
        file_dict = load_json(file)
        do_request(file_dict)


def create_file(data) -> None:
    """
    Método para crear un fichero con extension html para comprobar lo que se descarga desde la petición
    :param data:
    :return:
    """
    with open('scrapy.html', 'w', encoding='utf-8') as f:
        f.write(str(data))


def do_request(data: list) -> None:
    for producto in data:
        seccion = producto['seccion']
        marca = producto['marca']
        url = producto['url']

        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'lxml')

        # Comprobar datos que se procesaran con BeautifulSoup
        #create_file(soup)

        title = soup.find(id="productTitle").get_text().strip()
        price = formatter_price(soup.find(id="priceblock_ourprice").get_text())

        # Generate Plantilla HTML para enviar por HTML


        send_email(url, price)


def formatter_price(price: str) -> float:
    # Eliminamos el char '€'
    # Eliminamos los espacion en blacon entre 'precio' y el signo '€'
    return price[:-1].strip()


def send_email(url:str , price: float) -> None:
    """
    Ejecutar el envio del aviso por email
    :param url: Url producto amazon que queremos monitorizar
    :param price: Precio del producto
    :return: None
    """
    server = smtplib.SMTP(getenv('SMTP'), getenv('PORT_SMTP'))
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(getenv('FROM'), getenv('PASSWORD'))

    subject = 'Control Pricing'
    body = f"Check the amazon link {url}"
    msg = f"Subject: {subject} \n\n Price: {price} \n\n {body}"

    # Create message container - the correct MIME type is multipart/alternative
    # Show email in format text/plain or text/html, so client can view it independently of the format
    # that has been configured in its viewer
    message = MIMEMultipart("alternative")
    message["Subject"] = "Control pricing Amazon"
    message["From"] = getenv('SMTP')
    message["To"] = 'javierpozcor@gmail.com'
    # Create the plain-text and HTML version of your message
    text = "Control Pricing\n---------------"

    data = {
        "price": price,
        "url": url
    }
    html = """\
    <html>
      <body>
        <table>
            <thead>
                <tr>
                    <th>Precio</th>
                    <th>Url</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{price}</td>
                    <td><a href="{url}">Ir</a></td>
                </tr>
            </tbody>
        </table>
      </body>
    </html>
    """.format(**data)

    # Turn these into plain/html MIMEText objects
    # Record de MIME types of both parts - text/plain and text/html
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container
    # According to RFC2046 the last part of a multipart message, in this case the HTML message,
    # is best and preferred
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)


    try:
        # server.sendmail('devjpozo@gmail.com', 'javierpozcor@gmail.com', msg)
        server.sendmail(getenv('FROM'), 'javierpozcor@gmail.com', message.as_string())
        print("Mensaje enviado!!")
    except Exception as e:
        print(f"No se pudo enviar el email. Error: {e}")

    server.quit()


if __name__ == "__main__":

    dir_root_app = Path().cwd()

    environ['ENV'] = 'DEV'
    environ['DIR_ROOT_APP'] = str(dir_root_app)
    load_dotenv(dotenv_path=str(dir_root_app / 'config' / '.env'))

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                 'Chrome/75.0.3770.100 Safari/537.36'

    headers = {
        "Content-Type": "text/html;charset=UTF-8",
        "User-Agent": user_agent
    }

    searching()
