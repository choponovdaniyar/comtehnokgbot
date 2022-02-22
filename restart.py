# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import sqlite3
import requests


def get_html():
        headers = {
            "user-agent" : UserAgent().random
        }
        index = requests.get(url = "https://comtehno.kg/timetable", headers= headers)
        index = BeautifulSoup(index.text, "lxml")
        hrefs = []
        url = index.find_all("a", class_ = "elementor-button-link")
        for link in url:
            text = link.find("span", class_ = "elementor-button-text")
            reg = r"^РАСПИСАНИЕ +[1-3] +КУРСА$"
            if text != None and re.search(reg, text.text):
                id = int(re.findall(r"[1-3]", text.text)[0])
                hrefs += [ f"{id}{link.attrs['href']}"]
                
        for href in hrefs:
            with open("html/course{}.html".format(href[0]), "w", encoding="utf-8") as f:
                resp = requests.get(url=href[1:], headers=headers)
                f.write(resp.text)

def main(course):
    con = sqlite3.connect("bot.db")
    cur =  con.cursor()

    with open(f"html/course{course}.html", "r", encoding="utf-8") as f:
        html = BeautifulSoup(f.read(), "lxml")
    tbody = html.find("tbody")
    tr = tbody.find_all("tr")   

    while tr[0].find("td").text != "Время":
        tr = tr[1:]
    #группы
    groups = list()
    for group_it in tr[0].find_all("td")[1:]:
        if group_it.text != "ауд.":
            groups += [group_it.text]
            cur.execute('SELECT * FROM group_')
            cur.execute(f"INSERT INTO group_(id, name, course) VALUES ( { len(cur.fetchall()) + 1}, '{group_it.text}', '{course}')")
            
        con.commit()
    else:   
        tr = tr[1:]
    
    wight = len(tr[0].find_all("td"))
    height = len(tr)
    table = list()
    td_tab = list()
    for x in range(height):
        table +=[[]]
        td_tab += [tr[x].find_all("td")]
        for y in range(wight):
            table[x] += [None]
 

    for x in range(height):
        for y in range(wight):
            if x > 0 and table[x - 1][y].attrs["rowspan"] != "1":
                table[x][y] = table[x - 1][y] 
                table[x][y]["rowspan"] = str(int(table[x][y]["rowspan"]) - 1)
            elif y > 0 and table[x][y - 1].attrs["colspan"] != "1":
                table[x][y] = table[x - 1][y] 
                table[x][y]["colspan"] = str(int(table[x][y]["colspan"]) - 1)
            else:
                
                table[x][y] = td_tab[x][0]
        
                if table[x][y].attrs.get("rowspan") == None:
                    table[x][y].attrs["rowspan"] = "1"
                if table[x][y].attrs.get("colspan") == None:
                    table[x][y].attrs["colspan"] = "1"
                if len(td_tab[x]) > 1:
                    td_tab[x] = td_tab[x][1:]
        
    for x in range(height):
        for y in range(wight):
            words = re.findall(r"[^ ]+", table[x][y].text)
            table[x][y] = (" ".join(words)).replace(": ", ":")
            if table[x][y] == "":
                table[x][y] = "- - -" 
        
    lesson_table = list()
    lesson_id = 0
    for x in range(height):
        time = table[x][1]
        day = table[x][0]
        lesson_id = -1 if (x > 0 and day != table[x-1][0]) else lesson_id
        if day == "- - -":
            break
        group_id = 0
        week = 1 if (x == 0 or time != table[x-1][1]) else 2
        lesson_id += int(x > 0 and time != table[x-1][1] and week == 1)
        lesson_id %= 4
        for y in range(2, wight,2):
            group  =  groups[group_id]
            group_id += 1
            lesson = table[x][y]
            classroom = table[x][y+1]

            reg = re.findall(r"[^ ]+", lesson)
            reg.reverse()
            teacher = "- - -"
            if len(reg) > 1 and reg != "- - -":
                id = 0
                while id < len(reg) and (len(reg[id]) <= 4 or len(re.findall(r"\.", reg[id])) > 1):
                    id += 1
                if id < len(reg):
                    id += int(reg[id] not in ["(пр.)", "(пр)", "(лек.)", "(лек)", "работа", "проект"])
                    teacher = " ".join([ x + "." if len(x) <= 2 else x for x in re.findall(r"[А-Яа-яA-Za-z]+", " ".join(reg[:id]).replace(".", " "))]).replace("кызы","к.").replace("уулу", "y.")
            row = [f"'{x}'" for x in[group, str(week), str(day), str(lesson_id + 1), str(time), teacher, lesson, classroom]]
            lesson_table += [ f'({", ".join(row)})']


    lesson = ", \n".join(lesson_table)
    cur.execute('''
        INSERT INTO lesson_
        VALUES 
        {}
    '''.format(lesson))
    con.commit()

    
    


def scrap_html():
    con = sqlite3.connect("bot.db")
    cur =  con.cursor()
    cur.execute("DELETE FROM group_")
    cur.execute("DELETE FROM lesson_")
    con.commit()
    for x in range(1, 3 +1):
        main(x)

def restart():
    get_html()
    scrap_html()

if __name__ == "__main__":
    restart()