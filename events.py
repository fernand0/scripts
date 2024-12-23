import arrow
import json
import locale
import os
import sys

from ics import Calendar
from datetime import datetime, timedelta

LOCAL = "local"
SEP = " , "
TIPOS = ["Magistral", "problemas", "laboratorio", "festivo", "evaluación"]


def translate(line):
    line = line.replace("Mo ", "L ").replace("Tu ", "M ")
    line = line.replace("We ", "X ")
    line = line.replace("Th ", "J ").replace("Fr ", "V ")

    return line

def translateSes(sesion):
    return sesion
    if sesion == "33":
        sesion = "inf01"
    elif sesion == "13":
        sesion = "inf02"
    elif sesion == "5":
        sesion = "inf03"
    elif sesion == "1":
        sesion = "inf04"
    elif sesion == "2":
        sesion = "inf05"
    elif sesion == "11":
        sesion = "inf06"
    elif sesion == "12":
        sesion = "inf07"
    elif sesion == "15":
        sesion = "inf08"
    elif sesion == "23":
        sesion = "inf09"
    elif sesion == "24":
        sesion = "inf10"
    elif sesion == "31":
        sesion = "inf11"
    elif sesion == "32":
        sesion = "inf12"
    elif sesion == "21":
        sesion = "inf13"
    elif sesion == "22":
        sesion = "inf14"
    elif sesion == "34":
        sesion = "inf15"
    elif sesion == "3":
        sesion = "inf16"
    elif sesion == "4":
        sesion = "inf17"

    return sesion

def readIcs(FICHERO_ICS):
    with open(FICHERO_ICS, "r") as f:
        c = Calendar("\n".join(f.readlines()))

    horario = {}
    # print(f"Eventos: {c.events}")
    for e in c.events:
        tieneTipo = False
        for tipo in TIPOS:
            if tipo in e.name:
                tieneTipo = True
                if not tipo in horario.keys():
                    horario[tipo] = {}
                if not e.name in horario[tipo].keys():
                    horario[tipo][e.name] = []
                horario[tipo][e.name].append(e)
        if not tieneTipo:
            print(f"Tipo {e.name} no considerado")

    # import pprint
    # pprint.pprint(f"Horario: {horario}")
    return horario

def datosGrupos(horario, startProb, startPrac):
    grupos = {}

    for tipo in TIPOS:
        problemas = False
        laboratorio = False
        if not tipo in horario:
            print(f"tipo no : {tipo}")
            continue
        for lineaGrupo in sorted(horario[tipo].keys()):
            name = horario[tipo][lineaGrupo][0].name
            print(f"Nnnname {name}")
            pos = name.find(" Grupo:")
            posF = name.find(" ", pos + 8)
            grupo = name[pos + 1 + 7 : posF]
            if len(grupo) > 3:
                grupo = grupo[:-1]
            elif len(grupo) < 2:
                grupo = f"0{grupo}"

            if "problemas" in name:
                sesion = f"Subgrupo-{name[pos+11:]}"
                problemas = True
            elif "laboratorio" in name:
                sesion = f"{name[pos+8:]}"
                sesNum = sesion.split("-")
                sesion = translateSes(sesNum[0][:-1])
                sesion = f"{sesion} - {sesNum[1]}"
                grupo = grupo.split(" ")[0]
                laboratorio = True
            else:
                sesion = name[pos + 13 :]

            if grupo not in grupos.keys():
                grupos[grupo] = []
            for dato in sorted(horario[tipo][lineaGrupo]):
                begin = dato.begin.to(LOCAL)
                end = dato.end.to(LOCAL)
                horas = (
                    f"{begin.format('ddd')} "
                    f"{begin.format('dd mmm, hh:mm')}-"
                    f"{end.format('hh:mm')}"
                )
                lugar = dato.location
                if problemas and begin >= startProb:
                    grupos[grupo].append(f"{begin};{end}; {sesion}; {lugar}")
                elif laboratorio and begin >= startPrac:
                    grupos[grupo].append(f"{begin};{end}; {sesion}; {lugar}")
                elif not problemas and not laboratorio:
                    grupos[grupo].append(f"{begin};{end}; {sesion}; {lugar}")

    return grupos

def location(loc):
    # https://sigeuz.unizar.es/?room=csf.1110.00.260
    pos = loc.find("CRE")
    loc = (
        loc[:pos]
        + "["
        + loc[pos : pos + 15]
        + "](https://sigeuz.unizar.es/?room="
        + loc[pos : pos + 15]
        + "))"
    )
    return loc

def buscarProfe(profes, grupo, tipo):
    if grupo in profes[tipo]:
        elProfe = profes[tipo][grupo]
    else:
        elProfe = "Profesor xxx"
    if not elProfe:
        elProfe = "Profesor xxx"
    return elProfe


def main():
    if (len(sys.argv))>1:
        DATADIR = sys.argv[1]
    else:
        DATADIR = "/home/ftricas/Documents/work/Asignaturas/FIM/fim-24-25/horarios"

    PROFES = f"{DATADIR}/profes.txt"
    if os.path.exists(f"{PROFES}"):
        with open(PROFES, 'r') as fProfes:
            profes = json.load(fProfes)
    else:
        profes = ""

    START = f"{DATADIR}/start.txt"
    locale.setlocale(locale.LC_TIME, "")
    if os.path.exists(f"{START}"):
        with open(START, "r") as fStart:
            lines = fStart.readlines()
        print(lines)
        startCourse = arrow.get(lines[0])
        if lines.count('\n')>1:
            pass
        else:
            startProb = startCourse
            startPrac = startCourse
    else:
        # Depende de la asignatura
        startCourse = arrow.Arrow(2025, 1, 22)
        startProb = startCourse.dehumanize("in 18 days")
        startPrac = startCourse.dehumanize("in 28 days")

    print(f"Course starts: {startCourse}")
    print(f"Problems start: {startProb}")
    print(f"Lab start: {startPrac}")

    for FICHERO_ICS in sorted(os.listdir(f"{DATADIR}")):
        if "PDS" in FICHERO_ICS and FICHERO_ICS.endswith("ics"):
            print(f"Fichero: {FICHERO_ICS}")
            horario = readIcs(FICHERO_ICS)

            grupos = datosGrupos(horario, startProb, startPrac)

            lastIni = ""
            for grupo in sorted(grupos.keys()):
                if lastIni != grupo[0]:
                    lastIni = grupo[0]
                    countG = 0
                # print(f"grupo-len: {grupo} {len(grupo)}")
                if len(grupo) < 3:
                    nameGrupo = translateSes(grupo)
                else:
                    nameGrupo = grupo
                # print(f"grupo-len: {int(nameGrupo):02} {len(nameGrupo)}")
                if nameGrupo.isnumeric():
                    nameGrupo = f"{int(nameGrupo):02}"
                if grupos[grupo]:
                    texto = ""
                    title = ""
                    place = ""
                    placeP = ["", "", ""]
                    if nameGrupo == "515":
                        continue
                    myDirR = f"{DATADIR}/result"
                    if not os.path.exists(myDirR):
                        input(f"directorio {myDirR} no existe. lo creamos? ")
                        os.mkdir(myDirR)
                    with open(f"{myDirR}/{nameGrupo}.csv", "w") as fGrupo:
                        first = True
                        dateW = 0
                        for linea in sorted(grupos[grupo]):
                            fields = linea.split(";")
                            if first:
                                if len(fields) > 3 and "laboratorio" in fields[2]:
                                    gr = fields[2].split("-")[0]
                                    if not 'None' in fields[3]:
                                        loc = fields[3].split("-")[1]
                                    else:
                                        loc = ""
                                    loc = location(loc)
                                    # pos = loc.find("CRE")
                                    # loc = (
                                    #     loc[:pos]
                                    #     + "["
                                    #     + loc[pos : pos + 15]
                                    #     + "](https://sigeuz.unizar.es/?room="
                                    #     + loc[pos : pos + 15]
                                    #     + "))"
                                    # )
                                    # if nameGrupo in profes['laboratorio']:
                                    #     elProfe = profes['laboratorio'][nameGrupo]
                                    # else:
                                    #     elProfe = "Profesor xxx"
                                    # if not elProfe:
                                    #     elProfe = "Profesor xxx"
                                    elProfe = buscarProfe(profes, nameGrupo, 'laboratorio')
                                    title = f"## Grupo {gr}. {elProfe}"
                                    place = f"\n* <u>{loc}</u>\n\n"
                                    place = f"\\ \n\\ \n{place}"
                                    place = f"\\ \n\\ \n{place}"
                                    linea = f"Fecha{SEP}Horario\n"

                                    texto = f"{texto}{linea}"
                                    fGrupo.write(linea)
                                    # fGrupo.write(f"fecha{SEP}horario{SEP}lugar\n")
                                    first = False
                                else:
                                    if len(fields) > 3:
                                        if not 'None' in fields[3]:
                                            loc = fields[3].split("-")[1]
                                        else:
                                            loc = fields[3]
                                        loc = location(loc)
                                        # pos = loc.find("CRE")
                                        # loc = (
                                        #     loc[:pos]
                                        #     + "["
                                        #     + loc[pos : pos + 15]
                                        #     + "](https://sigeuz.unizar.es/?room="
                                        #     + loc[pos : pos + 15]
                                        #     + "))"
                                        # )
                                        # if nameGrupo in profes['teoria']:
                                        #     elProfe = profes['teoria'][nameGrupo]
                                        # else:
                                        #     elProfe = "Profesor xxx"
                                        elProfe = buscarProfe(profes, grupo, 'teoria')
                                        title = (
                                            f"# Grupo {nameGrupo}. \n\n"
                                            f"* Profesor: {elProfe}. "
                                            f"{loc}\n\n"
                                        )

                                        # linea = f"{SEP}{SEP}Teoría y problemas{SEP}{SEP}\n"
                                        linea = f"Semana{SEP}Fecha{SEP}Horario{SEP}tipo\n"
                                        texto = f"{texto}{linea}"
                                        fGrupo.write(linea)
                                        first = False
                            # fGrupo.write('\n\n\n')

                            startDate = datetime.strptime(
                                fields[0][:-6], "%Y-%m-%dt%H:%M:%S"
                            )
                            endDate = datetime.strptime(fields[1][:-6], "%Y-%m-%dt%H:%M:%S")

                            line = (
                                f"{startDate.ctime()[:2]} "
                                f"{startDate.day}/{startDate.month}{SEP} "
                                f"{startDate.hour}:00-{endDate.hour}:00"
                            )
                            if not "laboratorio" in fields[2]:
                                weekN = startDate.isocalendar()[1]
                                if weekN > dateW and not first:
                                    startM = startDate - timedelta(days=startDate.weekday())
                                    endF = startDate + timedelta(days=5-startDate.weekday())
                                    line = (f"{startM.day}/{startM.month}" # Semana
                                            f"-{endF.day}/{endF.month}{SEP}{line}")
                                    dateW = startDate.isocalendar()[1]
                                else:
                                    line = f"{SEP}{line}"
                            line = translate(line)
                            texto = f"{texto}{line}"
                            fGrupo.write(line)
                            if "laboratorio" in fields[2]:
                                for elem in fields[3:-1]:
                                    line = f"{SEP}{elem}"
                                    texto = f"{texto}{line}"
                                    fGrupo.write(line)
                            else:
                                for elem in fields[2:-1]:
                                    line = f"{SEP}{elem}"
                                    texto = f"{texto}{line}"
                                    fGrupo.write(line)
                                if "Subgrupo" in fields[2]:
                                    # print(f"ffffields: {fields[2].split('-')}")
                                    pos = int(fields[2].split("-")[1]) - 1
                                    nG = f"{nameGrupo}{pos+1}"
                                    loc = fields[3].split("-")[1]
                                    loc = location(loc)
                                    # posL = loc.find("CRE")
                                    # loc = (
                                    #     loc[:posL]
                                    #     + "["
                                    #     + loc[posL : posL + 15]
                                    #     + "](https://sigeuz.unizar.es/?room="
                                    #     + loc[posL : posL + 15]
                                    #     + ") )" # 🔗
                                    # )
                                    # # https://sigeuz.unizar.es/?room=csf.1110.00.260
                                    # if nG in profes['problemas']:
                                    #     elProfe = profes['problemas'][nG]
                                    # if not elProfe:
                                    #     elProfe = "Profesor xxx"
                                    elProfe = buscarProfe(profes, nG, 'problemas')
                                    placeP[pos] = (
                                        f"  * Subgrupo de problemas {nG}. {elProfe}."
                                        f" <u>{loc}</u>"
                                    )

                            texto = f"{texto}\n"

                            fGrupo.write("\n")
                        # fGrupo.write("----------------------------------------" "\n")

                        # for i in range(3):
                        #     nG = f"{nameGrupo}{i+1}"
                        #     title = f"{title}## Subgrupo de problemas {nG}. {profes['problemas'][nG]}\n\n"

                        texto = f"{texto}\n\n{title}"

                    import subprocess

                    myDirM = f"{DATADIR}/md"
                    if not os.path.exists(myDirM):
                        input(f"directorio {myDirM} no existe. lo creamos? ")
                        os.mkdir(myDirM)

                    subprocess.run(
                        [
                            "pandoc",
                            "-s",
                            "-o",
                            f"{myDirM}/{nameGrupo}.md",
                            f"{myDirR}/{nameGrupo}.csv",
                        ]
                    )

                    with open(f"{myDirM}/{nameGrupo}.md", "r") as f:
                        data = f.read()
                    with open(f"{myDirM}/{nameGrupo}.md", "w") as f:
                        f.write(f"{title}") #\n\n")
                        if place:
                            f.write(f"{place}\n\n")
                        else:
                            for i in range(3):
                                f.write(f"{placeP[i]}\n\n")
                        f.write("\\ \n\\ \n")
                        f.write("\\ \n\\ \n")
                        f.write("\n\n")
                        if not "Sala" in place:
                            f.write("## Calendario:\n\n")
                            f.write("\\ \n\\ \n")
                            f.write("\\ \n\\ \n")
                            f.write("\n\n")

                        f.write(data)
                        f.write("\n\n")
                        if len(nameGrupo) == 2:
                            countG = countG + 1

                        if countG==3 or len(nameGrupo) == 3:
                            f.write("\\pagebreak\n\n")
                            countG = 0

                    # with open(f"result/j{nameGrupo}.csv", "w") as fGrupo:
                    #     for linea in sorted(grupos[grupo]):
                    #         if "laboratorio" in linea:
                    #             fields = linea.split(";")
                    #             lugar = fields[3]
                    #             # print(f"Lugar: {lugar}")
                    #             date = datetime.strptime(fields[0][:10], "%Y-%m-%d")
                    #             date = str(date)[:-9]
                    #             startDate = datetime.strptime(fields[0][11:-6], "%H:%M:%S")
                    #             endDate = datetime.strptime(fields[1][11:-6], "%H:%M:%S")
                    #             line = (
                    #                 f"{lugar};{date};" f"{startDate.hour}:00-{endDate.hour}:00;"
                    #             )

                    #             # print(f"Line: {line}")
                    #             fGrupo.write(line)
                    #             fGrupo.write("\n")


    labs = {}
    teor = {}
    for FICHERO_CSV in sorted(os.listdir(f"{myDirR}")):
        if FICHERO_CSV[0].isnumeric():
            # Groups: 3 numbers. Lab subgroups: 2 numbers
            # 3 + 4 = 7 ('.csv')
            # 2 + 4 = 6 ('.csv')
            if len(FICHERO_CSV) == 6:
                with open(f"{myDirR}/{FICHERO_CSV}", "r") as fLab:
                    data = fLab.read()
                    num = data.count("\n")
                    pos = data.find("\n") + 1
                    pos = data.find("\n", pos) + 1
                    pos = data.find("\n", pos) + 1
                    pos = data.find("\n", pos) + 1
                    # print(f"({FICHERO_CSV}) {data[pos]}: {num}")
                    if not data[pos] in labs:
                        labs[data[pos]] = []
                    labs[data[pos]].append((FICHERO_CSV[:-4], num))
            elif len(FICHERO_CSV) == 7:
                with open(f"{myDirR}/{FICHERO_CSV}", "r") as fLab:
                    data = fLab.read()
                    numM = data.count("Clase Magistral")
                    if not FICHERO_CSV in teor:
                        teor[FICHERO_CSV] = []
                    teor[FICHERO_CSV].append(numM)
                    for i in range(3):
                        numS = data.count(f"Subgrupo-{i+1}")
                        if not FICHERO_CSV in teor:
                            teor[FICHERO_CSV] = []
                        teor[FICHERO_CSV].append(numS)

    msg = "Laboratorio:"
    print("-"*len(msg))
    print(msg)
    print("-"*len(msg))
    for d in ["L", "M", "X", "J", "V"]:
        if d in labs:
            print(f"Day: {d}")
            for s in labs[d]:
                print(f" - {s[1]:02}: ({s[0]})")

    msg = "Teoría y Problemas:"
    print("-"*len(msg))
    print(msg)
    print("-"*len(msg))
    print(teor.keys())
    for g in teor.keys():
        print(f" - {teor[g]} ({g[:-4]})")

if __name__ == '__main__':
    main()

