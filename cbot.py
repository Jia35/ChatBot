import re
import time
import json
import random
from gtts import gTTS
from pygame import mixer


class ChatBot(object):
    """對話機器人

    signon() -> 登錄
    get_input() -> 讀取使用者輸入
    respond() -> 對話回應
    bot_quit() -> 保存使用者輸入到
    save_unknown_input() -> 保存未知輸入
    """
    def __init__(self, bot_name="Chatterbot"):
        self.curr_input = ""        # 當前輸入
        self.prev_input = ""        # 前一個輸入
        self.backup_input = ""      # 備份輸入
        self.curr_response = ""     # 當前回應
        self.prev_response = ""     # 前一個回應
        self.curr_context = ""      # 當前上下文
        self.prev_context = ""      # 前一個上下文
        self.subject = ""
        self.curr_event = ""
        self.prev_event = ""
        self.response_list = []     # 回應列表
        self.is_quit_program = False     # 是否結束程式
        self.curr_keyword = ""
        self.response_log = []
        self.list_unknown_input = []
        self.bot_name = bot_name

        with open('KnowledgeBase.json', 'r') as file:
            self.knowledge_base = json.load(file)

    def signon(self):
        """ 登錄 """
        self.handle_event("SIGNON**")
        self.select_response()
        self.save_log()
        self.save_log("CHATTERBOT")
        self.print_response()

    def get_input(self):
        """ 取得用戶輸入 """
        self.save_prev_input()
        self.curr_input = input("> ")      
        self.curr_input = self.preprocess_input(self.curr_input)
        self.save_log("USER")
    
    def respond(self):
        """ 處理機器人的所有響應，無論是用於事件還是僅用於當前用戶輸入 """
        self.save_prev_response()
        self.set_event("BOT UNDERSTAND**")

        if self.null_input():
            self.handle_event("NULL INPUT**")
        elif self.null_input_repetition():
            self.handle_event("NULL INPUT REPETITION**")
        elif self.user_repeat():
            self.handle_user_repetition()
        else:
            self.find_match()
        
        if self.user_want_to_quit():
            self.is_quit_program = True
        
        if not self.bot_understand():
            self.handle_event("BOT DON'T UNDERSTAND**")
            self.update_unkown_input_list()
        
        if len(self.response_list) > 0:
            self.select_response()
            # self.save_bot_response()
            self.preprocess_response()
            if self.bot_repeat():
                self.handle_repetition()

            self.save_log("CHATTERBOT")
            # self.word_to_sound(self.curr_response)
            self.print_response()
    

    def handle_repetition(self):
        """ 處理程序的重複 """
        if len(self.response_list) > 0:
            self.response_list = self.response_list.pop(0)
        
        if self.no_response:
            self.save_input()
            self.set_input(self.curr_event)

            self.find_match()
            self.restore_input()

        self.select_response()

        # if len(self.response_list) > 1:
        #     s = self.response_log.copy()

    def handle_user_repetition(self):
        """ 處理用戶的重複 """
        if self.same_input():
            self.handle_event("REPETITION T1**")
        elif self.similar_input():
            self.handle_event("REPETITION T2**")

    def handle_event(self, event):
        """ 處理事件
        
        Args:
            event: (string)事件名稱
        """
        self.save_prev_event()
        self.set_event(event)

        self.save_input()
        event = " " + event + " "
        self.set_input(event)

        if not self.same_event():
            self.find_match()

        self.restore_input()

    def clean_string(self, text):
        """ 刪除標點符號、重複空格 """
        # text = re.sub("[?!@#$%^&*()/_\+-=~:.\'\"！？，。、￥…（）：]+", "", text)
        text = re.sub("[?!.;,*~]+", "", text)

        temp = ""
        prev_char = " "
        for char in text:
            if not(char == " " and prev_char == " "):
                temp += char
                prev_char = char
        return temp

    def preprocess_input(self, text):
        """ 對輸入預處理，刪除標點符號、重複空格，及將輸入轉換為大寫 """
        temp = self.clean_string(text)
        temp = temp.upper()
        text = " " + temp + " "
        return text

    def preprocess_response(self):
        """ 對回應預處理，針對有*星號的回應 """
        if self.curr_response.find("*") != -1:
            self.find_subject()
            self.subject = self.transpose(self.subject)
            self.curr_response = self.curr_response.replace("*", self.subject)

    def find_subject(self):
        """ 擷取去掉keyword後的輸入 """
        self.subject = ""
        self.curr_input = self.curr_input.rstrip()
        pos = self.curr_input.find(self.curr_keyword)
        if pos != -1:
            self.subject = self.curr_input[pos + len(self.curr_keyword) - 1:]

    def transpose(self, str_input):
        """轉換字串

        英文人稱的轉換

        Args:
            str_input: (string)待轉換的字串
        Returns:
            str_input: (string)轉換後的字串
        """
        transpos_list = [
            [" MYSELF ", " YOURSELF "],
            [" DREAMS ", " DREAM "],
            [" WEREN'T ", " WASN'T "],
            [" AREN'T ", " AM NOT "],
            [" I'VE ", " YOU'VE "],
            [" MINE ", " YOURS "],
            [" MY ", " YOUR "],
            [" WERE ", " WAS "],
            [" MOM ", " MOTHER "],
            [" I AM ", " YOU ARE "],
            [" I'M ", " YOU'RE "],
            [" DAD ", " FATHER "],
            [" AM ", " ARE "],
            [" I'D ", " YOU'D "],
            [" I ", " YOU "],
            [" ME ", " YOU "]]

        is_transposed = False
        for transpos in transpos_list:
            first = transpos[0]
            second = transpos[1]
            pos = 0
            while pos != -1:
                str_input = str_input.replace(first, second)
                pos = str_input.find(first)
                if pos != -1:
                    is_transposed = True

        if not is_transposed:
            for transpos in transpos_list:
                first = transpos[0]
                second = transpos[1]
                pos = 0
                while pos != -1:
                    str_input = str_input.replace(first, second)
                    pos = str_input.find(first)

        return str_input

    def wrong_location(self, keyword, first_char, last_char, pos):
        """ 是否輸入中的keyWord與資料庫中的keyWord位置不同
        
        Args:
            keyword: (list)預處理過的keyWord
            first_char: (string)keyWord第一個字元
            last_char: (string)keyWord最後一個字元
            pos: (int)輸入字串中keyWord出現的位置
        """
        is_wrong_pos = False
        pos += len(keyword)
        if ( (first_char == '_' and last_char == '_' and self.curr_input != keyword) or
             (first_char != '_' and last_char == '_' and pos != len(self.curr_input)) or
             (first_char == '_' and last_char != '_' and pos == len(self.curr_input)) ):
            is_wrong_pos = True
        return is_wrong_pos

    def wrong_context(self, context_list):
        """ 是否回應的上文在上一次回應中

        Args:
            context_list: (list)回應的context列表
        """
        is_wrong_context = True
        if len(context_list) == 0:
            is_wrong_context = False
        else:
            temp_context = self.prev_response
            temp_context = self.clean_string(temp_context)
            for context in context_list:
                if context == temp_context:
                    self.prev_context = self.curr_context
                    self.curr_context = temp_context
                    is_wrong_context = False
                    break

        if len(self.prev_context) > len(self.curr_context):
            is_wrong_context = True
        
        return is_wrong_context


    def find_match(self):
        """ 查找當前輸入的回應 """
        self.response_list[:] = []
        best_keyword = ""
        response_list_temp = []

        for knowledge in self.knowledge_base:
            context_list = knowledge.get("context", [])
            for keyword in knowledge["problem"]:
                first_char = keyword[0]
                last_char = keyword[-1]
                keyword = keyword.strip("_")

                keyword = " " + keyword + " "

                keyPos = self.curr_input.find(keyword)

                if keyPos != -1:
                    if self.wrong_location(keyword, first_char, last_char, keyPos):
                        continue

                    if self.wrong_context(context_list):
                        continue

                    if len(keyword) > len(best_keyword):
                        best_keyword = keyword
                        response_list_temp[:] = []
                        response_list_temp.append(knowledge["reply"])

                    elif len(keyword) == len(best_keyword):
                        response_list_temp.append(knowledge["reply"])
        
        if len(response_list_temp) > 0:
            self.curr_keyword = best_keyword
            random.shuffle(response_list_temp)
            self.response_list = response_list_temp[0].copy()
            self.curr_response = self.response_list[0]

    # -------------
    def select_response(self):
        """ 隨機排列response_list後，挑第一個回應 """
        if self.bot_understand():
            random.shuffle(self.response_list)
            self.curr_response = self.response_list[0]

    def save_prev_input(self):
        self.prev_input = self.curr_input

    def save_prev_response(self):
        self.prev_response = self.curr_response
    
    def save_prev_event(self):
        self.prev_event = self.curr_event

    def set_event(self, event):
        self.curr_event = event

    def save_input(self):
        self.backup_input = self.curr_input

    def set_input(self, input_str):
        self.curr_input = input_str

    def restore_input(self):
        """ 將先前保存backup_input的值恢復到變量curr_input """
        self.curr_input = self.backup_input

    def print_response(self):
        if len(self.curr_response) > 0:
            response_temp = self.curr_response
            response_temp = response_temp.lower()
            s = response_temp[:1].upper()
            response_temp = s + response_temp[1:]
            print(response_temp)

    def save_bot_response(self):
        if self.curr_response:
            self.response_log.insert(self.curr_response)

    # --------------------------------
    def bot_repeat(self):
        """ 是否機器人已開始重複自己 """
        return (len(self.prev_response) > 0 and
                self.curr_response == self.prev_response)
        
    #     pos = self.findRespPos(self.curr_response)
    #     if pos > 0:
    #         return (pos + 1) < len(self.response_list)
    #     return False

    # def findRespPos(self, input_str):
    #     pos = -1
    #     s = self.response_log.copy()
    #     while len(s) == 0:
    #         pos += 1
    #         if s[0] == input_str:
    #             break
    #         s.pop(0)
    #     return pos

    
    def user_repeat(self):
        """ 是否用戶已開始重複自己 """
        return (len(self.prev_input) > 0 and
                (self.curr_input == self.prev_input or
                 self.curr_input.find(self.prev_input) != -1 or
                 self.prev_input.find(self.curr_input) != -1))
    
    def bot_understand(self):
        """ 是否機器人理解當前用戶輸入 """
        return len(self.response_list) > 0
        
    def null_input(self):
        """ 是否當前用戶輸入(curr_input)為null """
        return (len(self.curr_input) == 0) and (len(self.prev_input) != 0)

    def null_input_repetition(self):
        """ 是否用戶重複了一些null輸入 """
        return (len(self.curr_input) == 0) and (len(self.prev_input) == 0)

    def user_want_to_quit(self):
        """ 是否用戶想退出當前會話('BYE') """
        return self.curr_input.find("BYE") != -1
        
    def same_event(self):
        """ 是否當前event(curr_event)與前一個(prev_event)相同 """
        return (len(self.curr_event) > 0) and (self.curr_event == self.prev_event)

    def no_response(self):
        """ 是否對當前輸入沒有回應response """
        return len(self.response_list) == 0

    def same_input(self):
        """ 是否當前input(curr_input)與前一個(prev_input)相同 """
        return (len(self.curr_input) > 0) and (self.curr_input == self.prev_input)

    def similar_input(self):
        """ 是否當前和以前的輸入相似
        (e.g.:'how are you'和'how are you doing'相似)
        """
        return (len(self.curr_input) > 0 and
                (self.curr_input.find(self.prev_input) != -1 or
                 self.prev_input.find(self.curr_input) != -1))
    
    def bot_quit(self):
        return self.is_quit_program

    # ------------------------
    def update_unkown_input_list(self):
        """ 添加輸入到未知列表 """
        self.list_unknown_input.append(self.curr_input)

    def save_unknown_input(self):
        """ 保存保存未知輸入 """
        with open("unknown.txt", "a") as f:
            for line in self.list_unknown_input:
                f.write(line + "\n")


    def save_log(self, log_str=""):
        """保存Log檔

        Args:
            log_str: (string)''->對話開頭；'CHATTERBOT'->機器人；'USER'->使用者
        """
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if log_str == "":
            logtext = "\n\n--------------------\n"
            logtext += "Conversation log - " + str(now_time) + "\n\n"
        elif log_str == "CHATTERBOT":
            logtext = self.curr_response + "\n"
        elif log_str == "USER":
            logtext = ">" + self.curr_input + "\n"

        with open("log.txt", "a") as f:
            f.write(logtext)

    def word_to_sound(self, text):
        """ 文字轉語音播放

        Args:
            text: (string)待轉語音的文字
        """
        tts = gTTS(text)
        tts.save("wordToSound.mp3")
        self.play_sound("wordToSound.mp3")

    def play_sound(self, file_name):
        """ 播放錄音
        
        Args:
            file_name: (string)要播放的音檔名
        """
        mixer.init()
        mixer.music.load(file_name)
        mixer.music.play()
        while mixer.music.get_busy() == True:
            continue
        mixer.music.stop()
        mixer.quit()


"""Fetches rows from a Bigtable.

Retrieves rows pertaining to the given keys from the Table instance
represented by big_table.

Args:
    keys: A sequence of strings representing the key of each table row
        to fetch.

Returns:
    A dict mapping keys to the corresponding table row data
    fetched. Each row is represented as a tuple of strings. For
    example:

    {'Serak': ('Rigel VII', 'Preparer'),
    'Zim': ('Irk', 'Invader'),
    'Lrrr': ('Omicron Persei 8', 'Emperor')}

    If a key from the keys argument is missing from the dictionary,
    then that row was not found in the table.
"""
