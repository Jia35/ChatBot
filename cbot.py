import re
import json
import random


class CBot():
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
        self.transposList = [
            ["I'M", "YOU'RE"],
            ["AM", "ARE"],
            ["WERE", "WAS"],
            ["I", "YOU"],
            ["ME", "YOU"],
            ["YOURS", "MINE"],
            ["YOUR", "MY"],
            ["I'VE", "YOU'VE"],
            ["AREN'T", "AM NOT"],
            ["WEREN'T", "WASN'T"],
            ["I'D", "YOU'D"],
            ["DAD", "FATHER"],
            ["MOM", "MOTHER"],
            ["DREAMS", "DREAM"],
            ["MYSELF", "YOURSELF"]]

        with open('KnowledgeBase.json', 'r') as file:
            self.Knowledge_Base = json.load(file)

    def signon(self):
        self.handle_event("SIGNON")
        self.select_response()
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
        text = re.sub("[?!.;,*]+", "", text)

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
            self.transpose(self.m_sSubject)

            self.m_sResponse, _ = self.replace(self.m_sResponse, "*", self.m_sSubject)


    def find_subject(self):
        self.m_sSubject = ""
        self.m_sInput = self.m_sInput.rstrip()
        pos = self.m_sInput.find(self.m_sKeyWord)
        if pos != -1:
            self.m_sSubject = self.m_sInput[pos + len(self.m_sKeyWord) - 1:]


    def replace(self, str_input, substr1, substr2):
        pos = str_input.find(substr1)
        if pos != -1:
            str_input = str_input[:pos] + str_input[pos+len(substr1):]
            str_input = str_input[:pos] + substr2 + str_input[pos:]
        return str_input, pos
    # def trimRight(self, str_input, delim):
    #     # size_t pos = str.find_last_not_of(delim);
    #     if pos != -1:
    #         str_input = str_input[:pos+1]

    def transpose(self, str_input):
        bTransposed = False
        for transpos in self.transposList:
            first = transpos[0]
            first = " " + first + " "
            second = transpos[1]
            second = " " + second + " "

            str_input, pos = self.replace(str_input, first, second)
            if pos != -1:
                bTransposed = True

        if not bTransposed:
            for transpos in self.transposList:
                first = transpos[0]
                first = " " + first + " "
                second = transpos[1]
                second = " " + second + " "

                str_input, pos = self.replace(str_input, first, second)


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
            self.m_sKeyWord = bestKeyWord;
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
        
        if len(self.response_list) > 0:
            self.select_response()
            self.preprocess_response()
            if self.bot_repeat():
                self.handle_repetition()

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

    # --------------------------------
    def bot_repeat(self):
        """ 是否機器人已開始重複自己 """
        return (len(self.m_sPrevResponse) > 0 and
                self.m_sResponse == self.m_sPrevResponse)
    
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
        """ 是否對當前輸入沒有回應 """
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

'''
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
