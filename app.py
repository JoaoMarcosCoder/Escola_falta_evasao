from flask import Flask, render_template, request, redirect
import pandas as pd

app = Flask(__name__)

PLANILHA = "Media_Alunos.xlsx"

# -----------------------------------------------
# Lê a planilha e retorna lista de alunos
# -----------------------------------------------
def ler_alunos():
    df = pd.read_excel(PLANILHA)
    alunos = []

    for i, linha in df.iterrows():

        # Pega as notas usando range
        notas = []
        for numero in range(1, 7):          # range(1,7) → 1,2,3,4,5,6
            coluna = "Nota" + str(numero)
            if coluna in df.columns:
                notas.append(float(linha[coluna]))

        aluno = {
            "indice"     : i,
            "nome"       : linha["Nome"],
            "media"      : float(linha["Media "]),
            "frequencia" : float(linha["Frequencia"]),
            "ocorrencias": int(linha["Ocorrencias"]),
            "baixa_renda": bool(linha["Baixa_renda"]),
            "trabalha"   : bool(linha["Trabalha"]),
            "notas"      : notas
        }
        alunos.append(aluno)

    return alunos


# -----------------------------------------------
# ALGORITMO 1 — Classificação de Risco (PBL 2)
# Usa: if, elif, else, and, or
# -----------------------------------------------
def classificar_risco(media, frequencia, ocorrencias, baixa_renda, trabalha):

    # VERMELHO - situações críticas
    if frequencia < 60:
        return "VERMELHO"

    if media < 5 and (baixa_renda or trabalha):
        return "VERMELHO"

    if ocorrencias >= 3 and frequencia < 75:
        return "VERMELHO"

    # AMARELO - situações de atenção
    if frequencia < 75:
        return "AMARELO"

    if media < 6:
        return "AMARELO"

    if ocorrencias >= 1 and (baixa_renda or trabalha):
        return "AMARELO"

    if baixa_renda and trabalha:
        return "AMARELO"

    # VERDE - tudo certo
    return "VERDE"


# -----------------------------------------------
# ALGORITMO 2 — Análise de Notas (PBL 3)
# Usa: for, range, break, continue
# -----------------------------------------------
def analisar_notas(notas):

    # PASSO 1: Calcular média real ignorando zeros (faltas)
    # O continue pula a nota zero e vai para a próxima
    soma    = 0
    validas = 0

    for nota in notas:
        if nota == 0:
            continue        # ← pula o zero (falta), não entra na soma
        soma    = soma + nota
        validas = validas + 1

    if validas > 0:
        media_real = round(soma / validas, 1)
    else:
        media_real = 0

    # PASSO 2: Calcular médias progressivas
    # A cada nota válida, calcula a média até aquele momento
    medias_progressivas = []

    for i in range(len(notas)):             # range(len(notas)) → 0,1,2,3,4,5
        if notas[i] == 0:
            continue                        # ← pula falta aqui também

        soma_ate  = 0
        count_ate = 0

        for j in range(i + 1):             # ← for dentro de for (loop aninhado)
            if notas[j] == 0:
                continue
            soma_ate  = soma_ate + notas[j]
            count_ate = count_ate + 1

        media_ate = round(soma_ate / count_ate, 1)
        medias_progressivas.append(media_ate)

    # PASSO 3: Detectar quedas consecutivas
    # O break para o loop quando encontra 3 quedas seguidas
    notas_validas   = []
    quedas_seguidas = 0
    alerta_critico  = False

    # Primeiro filtra os zeros
    for nota in notas:
        if nota != 0:
            notas_validas.append(nota)

    # Agora percorre as notas válidas procurando quedas
    for i in range(1, len(notas_validas)):  # range(1, len) → começa em 1
        if notas_validas[i] < notas_validas[i - 1]:
            quedas_seguidas = quedas_seguidas + 1

            if quedas_seguidas >= 3:
                alerta_critico = True
                break           # ← para o loop: encontrou 3 quedas seguidas!

        else:
            quedas_seguidas = 0 # reinicia se não caiu

    # PASSO 4: Identificar tendência
    tendencia = "ESTÁVEL"

    if len(notas_validas) >= 2:
        primeira = notas_validas[0]
        ultima   = notas_validas[-1]

        if ultima > primeira:
            tendencia = "MELHORANDO"
        elif ultima < primeira:
            tendencia = "PIORANDO"

    return {
        "media_real"          : media_real,
        "medias_progressivas" : medias_progressivas,
        "tendencia"           : tendencia,
        "alerta_critico"      : alerta_critico,
        "notas_validas"       : notas_validas
    }


# -----------------------------------------------
# PÁGINA PRINCIPAL — lista todos os alunos
# -----------------------------------------------
@app.route("/")
def index():
    alunos = ler_alunos()

    for aluno in alunos:
        aluno["risco"] = classificar_risco(
            aluno["media"],
            aluno["frequencia"],
            aluno["ocorrencias"],
            aluno["baixa_renda"],
            aluno["trabalha"]
        )
        aluno["analise"] = analisar_notas(aluno["notas"])

    return render_template("index.html", alunos=alunos)


# -----------------------------------------------
# DETALHE de um aluno
# -----------------------------------------------
@app.route("/aluno/<int:indice>")
def ver_aluno(indice):
    alunos = ler_alunos()
    aluno  = alunos[indice]

    aluno["risco"]   = classificar_risco(
        aluno["media"], aluno["frequencia"], aluno["ocorrencias"],
        aluno["baixa_renda"], aluno["trabalha"]
    )
    aluno["analise"] = analisar_notas(aluno["notas"])

    return render_template("aluno.html", aluno=aluno)


# -----------------------------------------------
# CADASTRAR novo aluno
# -----------------------------------------------
@app.route("/novo", methods=["GET", "POST"])
def novo_aluno():
    if request.method == "POST":
        df = pd.read_excel(PLANILHA)

        notas = []
        for numero in range(1, 7):
            valor = request.form.get("nota" + str(numero), "")
            if valor == "":
                notas.append(0.0)
            else:
                notas.append(float(valor))

        nova_linha = {
            "Nome"       : request.form["nome"],
            "Media "     : round(sum(n for n in notas if n != 0) /
                                 max(sum(1 for n in notas if n != 0), 1), 1),
            "Frequencia" : float(request.form["frequencia"]),
            "Ocorrencias": int(request.form["ocorrencias"]),
            "Baixa_renda": "baixa_renda" in request.form,
            "Trabalha"   : "trabalha"    in request.form,
            "Nota1": notas[0], "Nota2": notas[1], "Nota3": notas[2],
            "Nota4": notas[3], "Nota5": notas[4], "Nota6": notas[5],
        }

        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        df.to_excel(PLANILHA, index=False)

        return redirect("/")

    return render_template("novo.html")


# -----------------------------------------------
# EXCLUIR aluno
# -----------------------------------------------
@app.route("/excluir/<int:indice>")
def excluir_aluno(indice):
    df = pd.read_excel(PLANILHA)
    df = df.drop(index=indice).reset_index(drop=True)
    df.to_excel(PLANILHA, index=False)
    return redirect("/")


# -----------------------------------------------
# FLUXOGRAMA
# -----------------------------------------------
@app.route("/fluxograma")
def fluxograma():
    return render_template("fluxograma.html")


# -----------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
