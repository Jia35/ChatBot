import re
import time
import json
import random
from gtts import gTTS
from pygame import mixer


class CBot(object):
    def __init__(self, bot_name):
        self.m_sInput = ""      # 輸入
        self.m_sResponse = ""   # 回應
        self.m_sPreviousInput = ""      # 前一個輸入
        self.m_sPreviousResponse = ""   # 前一個回應
        self.m_sContext = ""
        self.m_sPrevContext = ""
        self.m_sEvent = ""
        self.response_list = []     # 回應列表
        self.bot_name = bot_name
        self.m_bQuitProgram = 0     # 是否結束程式
        self.m_sKeyWord = ""
        self.vResponseLog = []
        self.list_unknown_input = []

        with open('KnowledgeBase.json', 'r') as file:
            self.Knowledge_Base = json.load(file)

    def signon(self):
        self.handle_event("SIGNON**")
        self.select_response()
        self.save_log()
        self.save_log("CHATTERBOT")
        self.print_response()

    def get_input(self):
        """ 取得用戶輸入 """
        self.save_prev_input()
        self.m_sInput = input("> ")
        # sInput = " How   are# you?"        
        self.m_sInput = self.preprocess_input(self.m_sInput)

    def cleanString(self, text):
        """ 刪除標點符號、冗餘空格 """
        # text = re.sub("[?!@#$%^&*()/_\+-=~:.\'\"！？，。、￥…（）：]+", "", text)
        text = re.sub("[?!.;,*~]+", "", text)

        temp = ""
        prevChar = " "
        for char in text:
            if not(char == " " and prevChar == " "):
                temp += char
                prevChar = char
        return temp

    def preprocess_input(self, text):
        """ 對輸入預處理，刪除標點符號、冗餘空格，及將輸入轉換為大寫 """
        temp = self.cleanString(text)
        self.m_sInput = self.m_sInput.rstrip(". ")
        temp = temp.upper()
        text = " " + temp + " "
        return text


    def preprocess_response(self):
        if self.m_sResponse.find("*") != -1:
            self.find_subject()
            self.m_sSubject = self.transpose(self.m_sSubject)
            self.m_sResponse = self.m_sResponse.replace("*", self.m_sSubject)


    def find_subject(self):
        """ 擷取去掉keyword後的輸入 """
        self.m_sSubject = ""
        self.m_sInput = self.m_sInput.rstrip()
        pos = self.m_sInput.find(self.m_sKeyWord)
        if pos != -1:
            self.m_sSubject = self.m_sInput[pos + len(self.m_sKeyWord) - 1:]

    def transpose(self, str_input):
        """轉換字串

        英文人稱的轉換

        Args:
            str_input: (string)待轉換的字串
        Returns:
            str_input: (string)轉換後的字串
        """
        transposList = [
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

        bTransposed = False
        for transpos in transposList:
            first = transpos[0]
            second = transpos[1]
            pos = 0
            while pos != -1:
                str_input = str_input.replace(first, second)
                pos = str_input.find(first)
                if pos != -1:
                    bTransposed = True

        if not bTransposed:
            for transpos in transposList:
                first = transpos[0]
                second = transpos[1]
                pos = 0
                while pos != -1:
                    str_input = str_input.replace(first, second)
                    pos = str_input.find(first)

        return str_input

    def wrong_location(self, keyword, firstChar, lastChar, pos):
        bWrongPos = False
        pos += len(keyword)
        if ( (firstChar == '_' and lastChar == '_' and self.m_sInput != keyword) or
             (firstChar != '_' and lastChar == '_' and pos != len(self.m_sInput)) or
             (firstChar == '_' and lastChar != '_' and pos == len(self.m_sInput)) ):
            bWrongPos = True
        return bWrongPos


    def wrong_context(self, contextList):
        bWrongContext = True
        if len(contextList) == 0:
            bWrongContext = False
        else:
            sContext = self.m_sPrevResponse
            sContext = self.cleanString(sContext)
            for context in contextList:
                if context == sContext:
                    self.m_sPrevContext = self.m_sContext
                    self.m_sContext = sContext
                    bWrongContext = False
                    break

        if len(self.m_sPrevContext) > len(self.m_sContext):
            bWrongContext = True
        
        return bWrongContext


    def find_match(self):
        """ 查找當前輸入的回應 """
        self.response_list[:] = []
        bestKeyWord = ""
        response_list_temp = []

        for knowledge in self.Knowledge_Base:
            contextList = knowledge.get("context", [])
            for keyWord in knowledge["problem"]:
                firstChar = keyWord[0]
                lastChar = keyWord[-1]
                keyWord = keyWord.strip("_")

                keyWord = " " + keyWord + " "

                keyPos = self.m_sInput.find(keyWord)

                if keyPos != -1:
                    if self.wrong_location(keyWord, firstChar, lastChar, keyPos):
                        continue

                    if self.wrong_context(contextList):
                        continue

                    if len(keyWord) > len(bestKeyWord):
                        bestKeyWord = keyWord
                        response_list_temp[:] = []
                        response_list_temp.append(knowledge["reply"])

                    elif len(keyWord) == len(bestKeyWord):
                        response_list_temp.append(knowledge["reply"])
        
        if len(response_list_temp) > 0:
            self.m_sKeyWord = bestKeyWord
            random.shuffle(response_list_temp)
            self.response_list = response_list_temp[0].copy()
            self.m_sResponse = self.response_list[0]

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
            self.m_bQuitProgram = 1
        
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
            # self.word_to_sound(self.m_sResponse)
            self.print_response()
    


    def handle_repetition(self):
        """ 處理程序的重複 """
        if len(self.response_list) > 0:
            self.response_list = self.response_list.pop(0)
        
        if self.no_response:
            self.save_input()
            self.set_input(self.m_sEvent)

            self.find_match()
            self.restore_input()

        self.select_response()

        # if len(self.response_list) > 1:
        #     s = self.vResponseLog.copy()


    def handle_user_repetition(self):
        """ 處理用戶的重複 """
        if self.same_input():
            self.handle_event("REPETITION T1**")
        elif self.similar_input():
            self.handle_event("REPETITION T2**")


    def handle_event(self, event):
        """ 處理事件 """
        self.save_prev_event()
        self.set_event(event)

        self.save_input()
        event = " " + event + " "
        self.set_input(event)

        if not self.same_event():
            self.find_match()

        self.restore_input()

    # -------------
    def select_response(self):
        """ 隨機排列response_list後，挑第一個回應 """
        if self.bot_understand():
            random.shuffle(self.response_list)
            self.m_sResponse = self.response_list[0]

    def save_prev_input(self):
        self.m_sPrevInput = self.m_sInput

    def save_prev_response(self):
        self.m_sPrevResponse = self.m_sResponse
    
    def save_prev_event(self):
        self.m_sPrevEvent = self.m_sEvent



    def set_event(self, event):
        self.m_sEvent = event

    def save_input(self):
        self.m_sInputBackup = self.m_sInput

    def set_input(self, input_str):
        self.m_sInput = input_str

    def restore_input(self):
        """ 將先前保存m_sInputBackup的值恢復到變量m_sInput """
        self.m_sInput = self.m_sInputBackup

    def print_response(self):
        if len(self.m_sResponse) > 0:
            print(self.m_sResponse)

    def save_bot_response(self):
        if self.m_sResponse:
            self.vResponseLog.insert(self.m_sResponse)

    # --------------------------------
    def bot_repeat(self):
        """ 是否機器人已開始重複自己 """
        return (len(self.m_sPrevResponse) > 0 and
                self.m_sResponse == self.m_sPrevResponse)
        
    #     pos = self.findRespPos(self.m_sResponse)
    #     if pos > 0:
    #         return (pos + 1) < len(self.response_list)
    #     return False

    # def findRespPos(self, input_str):
    #     pos = -1
    #     s = self.vResponseLog.copy()
    #     while len(s) == 0:
    #         pos += 1
    #         if s[0] == input_str:
    #             break
    #         s.pop(0)
    #     return pos

    
    def user_repeat(self):
        """ 是否用戶已開始重複自己 """
        return (len(self.m_sPrevInput) > 0 and
                (self.m_sInput == self.m_sPrevInput or
                 self.m_sInput.find(self.m_sPrevInput) != -1 or
                 self.m_sPrevInput.find(self.m_sInput) != -1)
        )
    
    def bot_understand(self):
        """ 是否機器人理解當前用戶輸入 """
        return len(self.response_list) > 0
        
    def null_input(self):
        """ 是否當前用戶輸入(m_sInput)為null """
        return (len(self.m_sInput) == 0 and len(self.m_sPrevInput) != 0)

    def null_input_repetition(self):
        """ 是否用戶重複了一些null輸入 """
        return (len(self.m_sInput) == 0 and len(self.m_sPrevInput) == 0)

    def user_want_to_quit(self):
        """ 是否用戶想退出當前會話('BYE') """
        return self.m_sInput.find("BYE") != -1
        
    def same_event(self):
        """ 是否當前event(m_sEvent)與前一個(m_sPrevEvent)相同 """
        return (len(self.m_sEvent) > 0 and self.m_sEvent == self.m_sPrevEvent)

    def no_response(self):
        """ 是否對當前輸入沒有回應response """
        return len(self.response_list) == 0

    def same_input(self):
        """ 是否當前input(m_sInput)與前一個(m_sPrevInput)相同 """
        return (len(self.m_sInput) > 0 and self.m_sInput == self.m_sPrevInput)

    def similar_input(self):
        """ 是否當前和以前的輸入相似
        (e.g.:'how are you'和'how are you doing'相似)
        """
        return (len(self.m_sInput) > 0 and
                (self.m_sInput.find(self.m_sPrevInput) != -1 or
                 self.m_sPrevInput.find(self.m_sInput) != -1)
        )
    
    def bot_quit(self):
        return self.m_bQuitProgram

    # ------------------------
    def update_unkown_input_list(self):
        self.list_unknown_input.append(self.m_sInput)

    def save_unknown_input(self):
        with open("unknown.txt", "a") as f:
            for line in self.list_unknown_input:
                f.write(line + "\n")


    def save_log(self, log_str=""):
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if log_str == "":
            logtext = "\n\n--------------------\n"
            logtext += "Conversation log - " + str(now_time) + "\n\n"
        elif log_str == "CHATTERBOT":
            logtext = self.m_sResponse + "\n"
        elif log_str == "USER":
            logtext = ">" + self.m_sInput + "\n"

        with open("log.txt", "a") as f:
            f.write(logtext)


    def word_to_sound(self, text):
        """ 文字轉語音播放
        param text: string 文字
        """
        tts = gTTS(text)
        tts.save("wordToSound.mp3")
        self.play_sound("wordToSound.mp3")

    def play_sound(self, file_name):
        """ 播放錄音
        param file_name: string 要播放音檔名
        """
        mixer.init()
        mixer.music.load(file_name)
        mixer.music.play()
        while mixer.music.get_busy() == True:
            continue
        mixer.music.stop()
        mixer.quit()

'''
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

def respond(self):
    """ 在影像中尋找aruco tag
        param image: numpy.ndarray 輸入影像
        return image_markers: numpy.ndarray 經過標記aruco tag的影像
        return max_id: int 最接近的aruco tag的ID        
        """
        self.m_sPreviousInput = self.m_sInput
        self.m_sPreviousResponse = self.m_sResponse

        self.get_input()
        self.m_sInput = self.preprocess_input(self.m_sInput)
        print(self.m_sInput)

        responses = self.find_match(self.m_sInput)
        print(":", end="")
    

        if (self.m_sInput == self.m_sPreviousInput) and (len(self.m_sInput) > 0):
            print("YOU ARE REPEATING YOURSELF.")
        elif self.m_sInput == "BYE":
            print("IT WAS NICE TALKING TO YOU USER, SEE YOU NEXT TIME!")
        elif len(responses) == 0:
            print("I'M NOT SURE IF I UNDERSTAND WHAT YOU ARE TALKING ABOUT.")
        else:
            self.m_sResponse = random.choice(responses)
            if self.m_sResponse == self.m_sPreviousResponse:
                responses.remove(self.m_sPreviousResponse)
                self.m_sResponse = random.choice(responses)
            print(self.m_sResponse)
'''
