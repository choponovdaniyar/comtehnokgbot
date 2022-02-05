from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import sqlite3
import re
import requests     

class DB():
    #decorator
    def __info(func_name):
        def actual_decorator(func):
            def wrapper(*args, **kwargs):
                print(f"[INFO] <start> {func_name}")
                func(*args, **kwargs)
                print(f"[INFO] <finish> {func_name}")
            return wrapper
        return actual_decorator
            

    #private
    def __init__(self, fn):
        self.__con = sqlite3.connect(fn)
        self.__cur = self.__con.cursor()
        
        #id's
        self.__group_id = 0
        self.__lesson_id = 0
        self.__lesson_time_id = 0
        self.__day_id = 0

        self.__all_tables = [
            "day_", 
            "group_",
            "lesson_", 
            "lesson_time_"
            ]
        
    def __clear(self):
        '''
            Очищает таблицы относящиеся к расписанию.
            Применяя приватную функцию __delete_table() 
        '''
        for x in self.__all_tables:
            self.__delete_table(x)
    
    def __get_href_on_excel_file(self):
        '''
            Получает текущие ссылки на excel-файлы:
            Открывает url = [https://comtehno.kg/timetable] и форматирует в bs4
            Из этого файла берет ссылки формате: {номер курса}{ссылка}
        '''

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
        return hrefs

    def __restart_html(self):
        '''
            Из-за того, что при обновлении расписания, обновляется и ссылка на страницу расписания.
            Мы переходим на статическую ссылку [https://comtehno.kg/timetable] и оттуда ищем нужные ссылки.
        '''
        hrefs = self.__get_href_on_excel_file()
        headers = {
            "user-agent" : UserAgent().random
        }
        for href in hrefs:
            with open("html/course{}.html".format(href[0]), "w", encoding="utf-8") as f:
                resp = requests.get(url=href[1:], headers=headers)
                f.write(resp.text)
    
    def __restart_timetable(self,course):
        '''
            Обновляет расписание данного курса
        '''
        def plus_time(a, t):
            c, m = map(int, a.split(':'))
            
            while t:
                m, t = m + 1, t - 1
                c += bool(m == 60)
                m %= 60
            return f"{'{:0>2}'.format(c)}:{'{:0>2}'.format(m)}" 
    

        with open(f"html/course{course}.html", "r", encoding="utf-8") as f:
            res = f.read()

        
        html = BeautifulSoup(res, "lxml")
        row = html.find("tbody").find_all("tr")
        #поиск и нахождения классов со цветом фона #ffffff/
        numerator = { x.split("{")[0] for x in re.findall(r'.s[0-9]+{[^}]+background-color:#ffffff[^}]+}.', res)}        
        #поиск и нахождения классов со цветом фона #e7e6e6/
        denominator = { x.split("{")[0] for x in re.findall(r'.s[0-9]+{[^}]+background-color:#e7e6e6[^}]+}.', res)}
        #поиск и нахождения классов со цветом фона #ffff99/
        classroom = { x.split("{")[0] for x in re.findall(r'.s[0-9]+{[^}]+background-color:#ffff99[^}]+}.', res)}


        self.__lesson_time_id = 1
        sec_week = list()   
        pos = -1
        week_day = 0
        start_group_id = self.__group_id
        elem = row[pos].find("td")
        
        while not(elem != None and elem.text == "Время"):
            pos += 1
            elem = row[pos].find("td")
        else:
            tds = row[pos].find_all("td")
            for x in range(1, len(tds), 2): 
                resp =  [''' SELECT * FROM {} WHERE name = {}'''.format(f"{'group_'}", f"'{tds[x].text}'")]       
                if not len(self.response(*resp)):
                    self.insert("group_", (self.__group_id, tds[x].text, course))
                finish_group_id = self.__group_id
                self.__group_id += 1
        
        for x in range(pos, len(row)):
            www = []
            finish_group_id = start_group_id 
            is_sec = int(len(sec_week) > 0)
            try:
                if int(row[x].find("td").attrs['rowspan']) > 2:
                    week_day += 1
            except:
                pass


            for cell in row[x].find_all("td"):
                if  f".{cell.attrs['class'][0]}" in numerator|denominator:

                    if is_sec == False and cell.attrs.get("rowspan") == None and len(denominator) > 0:
                        sec_week += [finish_group_id]
                    
                    reg = re.findall(r"[^ ]+", cell.text)
                    reg.reverse()

                    lesson = reg
                    if len(reg) > 1:
                        id = 0
                        while id < len(reg) and (len(reg[id]) <= 4 or len(re.findall(r"\.", reg[id])) > 1):
                            id += 1
                        id += int(reg[id] not in ["(пр.)", "(пр)", "(лек.)", "(лек)", "работа"])
                        lesson = reg[id:]
                        teacher = " ".join([ x + "." if len(x) <= 2 else x for x in re.findall(r"[А-Яа-яA-Za-z]+", " ".join(reg[:id]).replace(".", " "))]).replace("кызы","к.").replace("уулу", "y.")
                    lesson.reverse()
                    lesson = " ".join(lesson)

                    lesson = "- - -" if not(lesson) else lesson

                    

                if f".{cell.attrs['class'][0]}" in classroom:
                    regs = [ 
                        r"[0-9][0-9]:[0-9][0-9]",
                        r"[0-9][0-9]: [0-9][0-9]",
                        r"[0-9]:[0-9][0-9]",
                        r"[0-9]: [0-9][0-9]",
                    ]
                    for reg in regs:
                        if not len(re.findall(reg,cell.text)):
                            continue
                        time = re.findall(reg,cell.text)[0]
                        time = ''.join(re.findall(r"[0-9:]",time))
                        time = ":".join(map(lambda x: '{:0>2}'.format(x),time.split(":")))
                        break

                    try:
                        cr = "- - -" 
                        if len(cell.text):
                            cr = re.findall(r"^[^:]+$",cell.text)[0]
                            

                        resp = ['SELECT * FROM {} WHERE name = {}'.format(f"{'lesson_'}", f"'{lesson}'")]
                        if len(self.response(*resp)) == 0:
                            if lesson == "- - -":
                                teacher = "- - -"
                                cr = "- - -"
                            self.insert("lesson_",(self.__lesson_id, lesson, teacher, cr))        
                            self.__lesson_id += 1
                        try:
                            
                            resp = 'SELECT * FROM {} WHERE start = {} AND course = {}'.format(f"{'lesson_time_'}",  f"'{time}'", f"{course}")
                            if len(self.response(resp)) == 0:
                                try:
                                    self.insert("lesson_time_", (course, self.__lesson_time_id, time, plus_time(time, 80)))
                                    self.__lesson_time_id += 1 
                                except Exception as e:
                                    print(1.1, e)
                        except Exception as e:
                            print(1, e)

                        if lesson != None:
                            try:
                                this_lesson_id = self.response(f"SELECT id FROM lesson_ WHERE name = '{lesson}'")
                                less_id = self.response("SELECT lesson FROM lesson_time_ WHERE course = {} AND start = '{}'".format(course, time))[0][0]
                                vals = [self.__day_id, 2 if is_sec else 1, week_day, sec_week[finish_group_id - start_group_id] if is_sec else finish_group_id, this_lesson_id[0][0],  less_id]
                                self.insert("day_", tuple(vals))
                                www += [[lesson, week_day, less_id]]
                                finish_group_id += 1
                                self.__day_id += 1
                            except Exception as e:
                                print(1,e)
                    except:
                        pass
            
            if is_sec:
                sec_week = list()

    def __delete_table(self,tn):
        try:
            self.response(f"DELETE FROM {tn} WHERE id >= 0")
        except:
            self.response(f"DELETE FROM {tn} WHERE course >= 0")
    
    #pablic
    @__info(func_name = "restart")
    def restart(self):
        self.__clear()
        self.__restart_html()

        for x in range(1,4):
            self.__lesson_time_id = 1
            self.__restart_timetable(x)   
            # print(f"[INFO] finish restart course #{x}")
     
     
    def response(self, *args, **kwargs):
        self.__cur.execute(*args, **kwargs)
        self.__con.commit()
        return self.__cur.fetchall()

    def insert(self,tn, tuple):
        self.__cur.execute(
        f'''
            INSERT INTO {tn}
            VALUES ({", ".join(["?"] * len(tuple))})
        ''', tuple)
        self.__con.commit()
