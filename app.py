import requests
import json
import time
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from getpass import getpass
from rich.console import Console
from rich.progress import Progress

propostas = {}
forms_candidatura_url = "https://moodle.isec.pt/moodle/mod/data/view.php?id=235588"

console = Console()
s = requests.Session()
moodle_adapter = HTTPAdapter(max_retries=5)
s.mount(forms_candidatura_url, moodle_adapter)

def get(url):
    while True:
        try:
            r = s.get(url, timeout=15)
        except:
            continue

        if r.status_code == 200:
            break
    return r

def post(url, data):
    while True:
        try:
            r = s.post(url, data=data, timeout=15)
        except:
            continue

        if r.status_code == 200:
            break
    return r

def login(user, password):
    with console.status("[bold yellow] A efetuar login...") as status:
        login_url = "https://moodle.isec.pt/moodle/login/index.php"
        r = get(login_url)
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {"name": "logintoken"})["value"]

        if(user.startswith("a") == False):
            user = "a" + user

        data = {
            "username": user,
            "password": password,
            "logintoken": token
        }

        r = post(login_url, data)
        time.sleep(0.3)

        if(r.url == "https://moodle.isec.pt/moodle/login/index.php"):
            return 401

        return r.status_code

def get_candidaturas(propostaId):
    candidaturas_url = f"https://moodle.isec.pt/moodle/mod/data/view.php?d=190&perpage=200&search={propostaId}&sort=2815&order=ASC&advanced=0&filter=1&f_2782=&f_2785="
    r = get(candidaturas_url)
    soup = BeautifulSoup(r.text, "html.parser")
    candidaturas = soup.find_all("div", {"class": "defaulttemplate"})
    if(len(candidaturas) == 0):
        return

    candidaturas.pop(0)
    propostas[propostaId] = []

    for candidatura in candidaturas:
        student = {}

        name = candidatura.find("table").find("tbody").findAll("tr")[0].findAll("td")[0].find("strong")
        if name:
            name.decompose()
            student["name"] = candidatura.find("table").find("tbody").findAll("tr")[0].findAll("td")[0].text[1:]

        number = candidatura.find("table").find("tbody").findAll("tr")[0].findAll("td")[1].find("strong")
        if number:
            number.decompose()
            student["number"] = candidatura.find("table").find("tbody").findAll("tr")[0].findAll("td")[1].text[2:]

        propostas[propostaId].append(student)

def get_propostas_by_aluno(aluno):
    propostas_aluno = []
    for proposta in propostas:
        for candidatura in propostas[proposta]:
            if candidatura["number"] == aluno:
                propostas_aluno.append(proposta)
    return propostas_aluno

def save_propostas():
    with open("data.json", "w") as f:
        f.write(json.dumps(propostas))
    f.close()
    console_print("[ ✓ ] Propostas guardadas com sucesso!", "green")

def console_print(message, color):
    console.print(f"[{color}]{message}[/]")

def console_prompt(message, color, password=False):
    return console.input(f"[{color}]{message}[/]", password=password)

if __name__ == "__main__":
    console_print("🚀  Bem-vindo ao CuscaEstagiosISEC!   ", "bold purple")
    user = console_prompt("[ > ] Introduza o seu número de aluno: ", "#85c2ff")
    password = console_prompt("[ > ] Introduza a sua password: ", "#85c2ff", password=True)
    
    if login(user, password) == 200:
        console_print("[ ✓ ] Login efetuado com sucesso!", "green")
    else: 
        console_print("[ X ] Erro ao efetuar login!", "red")
        exit()

    rangePropostas = console_prompt("\n[ > ] Introduza o intervalo de propostas que pretende pesquisar (ex: 1-10): ", color="#85c2ff")
    rangePropostas = rangePropostas.split("-")

    with Progress() as progress:
        task1 = progress.add_task("[bold yellow][ • ] A pesquisar propostas...", total=int(rangePropostas[1]) - int(rangePropostas[0]))
        for i in range(int(rangePropostas[0]), int(rangePropostas[1]) + 1, 1):
            get_candidaturas(f"P{i:03d}")
            progress.update(task1, description=f"[bold yellow][ • ] A pesquisar proposta P{i:03d}", advance=1)

        progress.update(task1, description=f"[bold green][ ✓ ] Propostas pesquisadas com sucesso!", advance=1)
        time.sleep(0.5)

    save_propostas()

    search_user = console_prompt("\n[ > ] Introduza o número de aluno que pretende pesquisar: ", color="#85c2ff")
    console_print(f"🔍 Propostas do aluno {search_user}:", "#fc6b03")
    aluno_propostas = get_propostas_by_aluno(search_user)
    if len(aluno_propostas) == 0:
        console_print(f"[ X ] Não foram encontradas propostas para o aluno {search_user}", "red")
    else:
        propostas_string = ""
        for proposta in aluno_propostas:
            propostas_string += f"{proposta}, "
        console_print(f"    {propostas_string[:-2]}", "#fc8003")