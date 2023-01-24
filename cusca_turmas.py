import requests
import json
import time
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from getpass import getpass
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt
from rich.panel import Panel


use_simple_term_menu = True
propostas = {}
forms_candidatura_url = "https://moodle.isec.pt/moodle/mod/data/view.php?id=265783-"
propostas_url = "https://moodle.isec.pt/moodle/mod/folder/view.php?id=265705"

try:
    from simple_term_menu import TerminalMenu
except:
    import inquirer
    use_simple_term_menu = False

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
    candidaturas_url = f"https://moodle.isec.pt/moodle/mod/data/view.php?d=214&perpage=10&search={propostaId}&sort=3217&order=ASC&advanced=0&filter=1&f_3217=&f_3220="
    r = get(candidaturas_url)
    soup = BeautifulSoup(r.text, "html.parser")
    candidaturas = soup.find_all("div", {"class": "defaulttemplate"})
    if(len(candidaturas) == 0):
        return

    candidaturas.pop(0)

    propostas[propostaId] = []

    for candidatura in candidaturas:
        student = {}

        student["name"] = candidatura.find("table").find("tbody").findAll("tr")[1].findAll("td")[0].text

        student["number"] = candidatura.find("table").find("tbody").findAll("tr")[1].findAll("td")[1].text

        # check if student already exists
        if student in propostas[propostaId]:
            continue
        propostas[propostaId].append(student)

def get_propostas_by_aluno(aluno):
    propostas_aluno = []
    for proposta in propostas:
        for candidatura in propostas[proposta]:
            if candidatura["number"] == aluno:
                propostas_aluno.append(proposta)
    return propostas_aluno

def get_alunos_on_proposta(proposta):
    alunos = []
    # check if proposta exists
    if proposta not in propostas:
        return alunos
    for candidatura in propostas[proposta]:
        alunos.append(candidatura)
    return alunos

def save_propostas():
    with open("data.json", "w") as f:
        f.write(json.dumps(propostas))
    f.close()
    console_print(f"[ ✓ ] Propostas guardadas com sucesso! ({len(propostas)})", "green")

def load_propostas():
    try:
        with open("data.json", "r") as f:
            global propostas
            propostas = json.loads(f.read())
        f.close()
        console_print("[ ! ] Encontrado ficheiro de propostas. A carregar...", "yellow")
        time.sleep(0.6)
        console_print("[ ✓ ] Propostas carregadas com sucesso!", "green")
    except:
        console_print("[ X ] Erro ao carregar propostas!", "red")

def procurarMoodleMenu():
    user = console_prompt("[ > ] Introduza o seu número de aluno: ", "#85c2ff")
    password = console_prompt("[ > ] Introduza a sua password: ", "#85c2ff", password=True)
    
    if login(user, password) == 200:
        console_print("[ ✓ ] Login efetuado com sucesso!", "green")
    else: 
        console_print("[ X ] Erro ao efetuar login!", "red")
        console_prompt("\nPressione qualquer tecla para voltar ao menu...", "#adadad")
        return

    rangePropostas = console_prompt("\n[ > ] Introduza o intervalo de propostas que pretende pesquisar (ex: 1-10): ", color="#85c2ff")
    rangePropostas = rangePropostas.split("-")

    with Progress() as progress:
        task1 = progress.add_task("[bold yellow][ • ] A pesquisar propostas...", total=int(rangePropostas[1]) - int(rangePropostas[0]))
        for i in range(int(rangePropostas[0]), int(rangePropostas[1]) + 1, 1):
            progress.update(task1, description=f"[bold yellow][ • ] A pesquisar proposta P{i:03d}")
            get_candidaturas(f"P{i:03d}")
            progress.update(task1, advance=1)

        progress.update(task1, description=f"[bold green][ ✓ ] Propostas pesquisadas com sucesso!", advance=1)
        time.sleep(0.5)

    save_propostas()
    console_prompt("\nPressione qualquer tecla para voltar ao menu...", "#adadad")

def procurarPropostasMenu():
    if(len(propostas) == 0):
        console_print("[ X ] Não foram encontradas propostas!", "red")
        load_propostas()
    search_proposta = console_prompt("\n[ > ] Introduza o número da proposta que pretende pesquisar: ", color="#85c2ff")
    if("P" not in search_proposta.upper()):
        search_proposta = "P" + search_proposta.zfill(3).upper()
    else:
        search_proposta = search_proposta[:1].upper() + search_proposta[1:].zfill(3).upper()
    console_print(f"🔍 Alunos na proposta {search_proposta}:", "#fc6b03")
    proposta_alunos = get_alunos_on_proposta(search_proposta)
    if len(proposta_alunos) == 0:
        console_print(f"[ X ] Não foram encontrados alunos na proposta {search_proposta}", "red")
    else:
        for proposta in proposta_alunos:
            console_print(f" - " + proposta["number"] + " (" + proposta["name"] + ")", "#fc8003")
    console_prompt("\nPressione qualquer tecla para voltar ao menu...", "#adadad")

def procurarAlunosMenu():
    if(len(propostas) == 0):
        console_print("[ X ] Não foram encontradas propostas!", "red")
        load_propostas()
    search_user = console_prompt("\n[ > ] Introduza o número de aluno que pretende pesquisar: ", color="#85c2ff")
    console_print(f"🔍 Propostas do aluno {search_user}:", "#fc6b03")
    aluno_propostas = get_propostas_by_aluno(search_user)
    if len(aluno_propostas) == 0:
        console_print(f"[ X ] Não foram encontradas propostas para o aluno {search_user}", "red")
    else:
        propostas_string = ""
        for proposta in aluno_propostas:
            propostas_string += f"{proposta}, "
        console_print(f"   {propostas_string[:-2]} ({len(aluno_propostas)})", "#fc8003")
    console_prompt("\nPressione qualquer tecla para voltar ao menu...", "#adadad")

def obterNomesPropostas():
    load_propostas()
    
    user = console_prompt("[ > ] Introduza o seu número de aluno: ", "#85c2ff")
    password = console_prompt("[ > ] Introduza a sua password: ", "#85c2ff", password=True)
    
    if login(user, password) == 200:
        console_print("[ ✓ ] Login efetuado com sucesso!", "green")
    else: 
        console_print("[ X ] Erro ao efetuar login!", "red")
        console_prompt("\nPressione qualquer tecla para voltar ao menu...", "#adadad")
        return
    
    r = get(propostas_url)
    soup = BeautifulSoup(r.text, "html.parser")
    propostas = soup.find_all("span", {"class": "fp-filename-icon"})

    for item in propostas:
        # example: 2022-P104-2S-DA-Mee-It-Projeto de Desenvolvimento - MES Mesprod.pdf
        # will always be 6 parts
        # 0 - year
        # 1 - proposal number
        # 2 - semester
        # 3 - course
        # 4 - company (can have spaces and "-" in it)
        # 5 - proposal name (can have spaces and "-" in it)"
        # ends with .pdf
        parts = item.text.split("-")
        year = parts[0]
        proposal_number = parts[1]
        semester = parts[2]
        course = parts[3]
        company = parts[4].strip()
        proposal_name = "".join(parts[5:]).replace(".pdf", "")

        proposal = {
            "year": year,
            "number": proposal_number,
            "semester": semester[0] + "º Semestre",
            "course": course,
            "company": company,
            "name": proposal_name,
            "candidaturas": []
        }

        console_print(f"[ ✓ ] Proposta {item.text} obtida com sucesso!", "green")
        console.print_json(json.dumps(proposal, indent=4, ensure_ascii=False))

    
    console_prompt("\nPressione qualquer tecla para voltar ao menu...", "#adadad")

def console_print(message, color, style="bold"):
    console.print(f"[{color}]{message}[/]", style=style)

def console_prompt(message, color, password=False):
    return console.input(f"[{color}]{message}[/]", password=password)

def main():
    console.clear()
    #console_print("🚀  Bem-vindo ao CuscaEstagiosISEC!")
    console.print(Panel("🚀  Bem-vindo ao CuscaEstagiosISEC!", style="bold purple", expand=False))
    options = ["[1] Pesquisar propostas no Moodle", "[2] Procurar propostas de um aluno", "[3] Consultar alunos numa proposta", "[4] Atualizar os nomes das propostas", "[5] Sair"]

    if use_simple_term_menu:
        console_print("O que pretende fazer?  ", "#c285ff")
        terminal_menu = TerminalMenu(options)
        menu_entry_index = terminal_menu.show()

        if menu_entry_index == None:
            # clear console rich
            console.clear()
            main()

        console_print(f"\n{(options[menu_entry_index])[4:]}:", "#c9b3ff")

        if menu_entry_index == 0:
            procurarMoodleMenu()
        elif menu_entry_index == 1:
            procurarAlunosMenu()
        elif menu_entry_index == 2:
            procurarPropostasMenu()
        elif menu_entry_index == 3:
            exit()

    else:
        options = [option[4:] for option in options]
        questions = [
            inquirer.List('menu',
                        message="O que pretende fazer?",
                        choices=options,
                        ),
        ]
        answers = inquirer.prompt(questions)

        console_print(f"{answers['menu']}", "#c9b3ff")

        if answers['menu'] == options[0]:
            procurarMoodleMenu()
        elif answers['menu'] == options[1]:
            procurarAlunosMenu()
        elif answers['menu'] == options[2]:
            procurarPropostasMenu()
        elif answers['menu'] == options[3]:
            obterNomesPropostas()
        elif answers['menu'] == options[4]:
            exit()

    main()

if __name__ == "__main__":
    main()