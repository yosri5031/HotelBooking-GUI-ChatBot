# -*- coding: utf-8 -*- 
"""Chatbot_v2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1GMtVnlMwFANd-G5ZUHf54stQfV6N-rUN 
"""

#from textblob import TextBlob  
#from attributegetter import *
import tkinter as tk
from tkinter import messagebox 
from generatengrams import ngrammatch
from Contexts import *
import json
from Intents import *
import random
import os
import re
from datetime import datetime
import pandas as pd
from PIL import ImageTk, Image


def performAction(intentname, params):
    if(intentname == "BookRestaurent"):
        df = pd.read_csv('data/restaurants.csv')
        df = df.drop('Address', axis=1)
        cusinecondition = df['cusine'].str.lower() == params['cusine'].lower()
        locationcondition = df['neighbourhood'].str.lower() == params['neighbourhood'].lower()
        costtypecondition = df['costtype'].str.lower() == params['costtype'].lower()
        df = df[cusinecondition & locationcondition & costtypecondition]
        if (df.empty == False):
            print(df)
        else:
            print("Sorry!!! NO Restaurants found with given information.Try Again!" )
    elif(intentname == "bookinghotel"):
        df = pd.read_csv('data/hotels.csv')
        df = df.drop('nights', axis=1)
        locationcondition = df['location'].str.lower() == params['location'].lower()
        roomtariffplancondition = df['roomtariffplan'].str.lower() == params['roomtariffplan'].lower()
        hotelclasscondition = df['hotelclass'].str.lower() == params['hotelclass'].lower()
        df = df[locationcondition & roomtariffplancondition & hotelclasscondition]
        if (df.empty == False):
            print(df)
        else:
            print("Sorry!!! NO Hotels found with given information.Try Again!" )  

def check_actions(current_intent, attributes, context):
    '''This function performs the action for the intent 
    as mentioned in the intent config file'''
    performAction(current_intent.action, attributes)
    context = IntentComplete()
    print("Your query is Completed. Try Another Options..")
    return 'action: ' + current_intent.action, context

def check_required_params(current_intent, attributes, context):
    '''Collects attributes pertaining to the current intent'''
    
    for para in current_intent.params:
        if para.required:
            if para.name not in attributes:
                #Example of where the context is born, implemented in Contexts.py
                if para.name=='nights':
                    context = validatenights()
                
                if para.name=='checkin':
                    context = validatecheckindate()  
                    
                #returning a random prompt frmo available choices.
                return random.choice(para.prompts), context 
                
    return None, context


def input_processor(user_input, context, attributes, intent):
    '''Spellcheck and entity extraction functions go here'''  
    
    #uinput = TextBlob(user_input).correct().string
    
    #update the attributes, abstract over the entities in user input
    attributes, cleaned_input = getattributes(user_input, context, attributes)
    
    return attributes, cleaned_input

def loadIntent(path, intent):
    with open(path) as fil:
        dat = json.load(fil)
        intent = dat[intent]
        return Intent(intent['intentname'],intent['Parameters'], intent['actions'])

def intentIdentifier(clean_input, context,current_intent):
    clean_input = clean_input.lower()
    
    #Scoring Algorithm, can be changed.
    scores = ngrammatch(clean_input)
        
    #choosing here the intent with the highest score
    scores = sorted_by_second = sorted(scores, key=lambda tup: tup[1])
    
    if(current_intent==None):
        return loadIntent('params/newparams.cfg',scores[-1][0])
    else:
        #If current intent is not none, stick with the ongoing intent
        return current_intent  

def getattributes(uinput,context,attributes):
    '''This function marks the entities in user input, and updates 
    the attributes dictionary'''
    #Can use context to context specific attribute fetching
    if context.name.startswith('IntentComplete'):
        return attributes, uinput
    else:
    #Code can be optimised here, loading the same files each time suboptimal 
        files = os.listdir('./entities/')
        entities = {}
        for fil in files:
            if (fil != '.ipynb_checkpoints'):
                lines = open('./entities/'+fil).readlines()
                for i, line in enumerate(lines):
                    lines[i] = line[:-1]
                entities[fil[:-4]] = '|'.join(lines)

    #Extract entity and update it in attributes dict
        for entity in entities:
            for i in entities[entity].split('|'):
                if i.lower() in uinput.lower():
                    attributes[entity] = i
        for entity in entities:
                uinput = re.sub(entities[entity],r'$'+entity,uinput,flags=re.IGNORECASE)

        #Example of where the context is being used to do conditional branching.
        if context.name=='validatenights' and context.active:
            match = re.search('([1-9]|1[031])$', uinput) #Validate nights for max 31 nights
            if match:
                uinput = re.sub('([1-9]|1[031])$', '$nights', uinput)
                attributes['nights'] = match.group()
                context.active = False  
                
        if context.name=='validatecheckindate' and context.active:
            regex = '(\d{2})[/.-](\d{2})[/.-](\d{4})$' 
            match = re.search(regex, uinput)  
            
            if match:
                try:
                    checkinDate = datetime.strptime(match.group(), "%d/%m/%Y")
                    if (checkinDate.date() >  datetime.now().date()):
                        uinput = re.sub(regex, '$checkin', uinput)
                        attributes['checkin'] = match.group()
                        context.active = False 
                    else:
                        print("Booking Date should be greater than today's date.")
                except ValueError:
                        print("Checkin Date is not in dd/mm/yyyy format")
        return attributes, uinput

class Session:
    def __init__(self, attributes=None, active_contexts=[FirstGreeting(), IntentComplete() ]):
        
        '''Initialise a default session'''
        
        #Active contexts not used yet, can use it to have multiple contexts
        self.active_contexts = active_contexts  
        
        #Contexts are flags which control dialogue flow, see Contexts.py           
        self.context = FirstGreeting()
        
        #Intent tracks the current state of dialogue
        #self.current_intent = First_Greeting()
        self.current_intent = None 
        
        #attributes hold the information collected over the conversation
        self.attributes = {}
        
    def update_contexts(self):
        '''Not used yet, but is intended to maintain active contexts'''
        for context in self.active_contexts:
            if context.active:
                context.decrease_lifespan()

    def reply(self, user_input):
        '''Generate response to user input'''
        
        self.attributes, clean_input = input_processor(user_input, self.context, self.attributes, self.current_intent) 
        self.current_intent = intentIdentifier(clean_input, self.context, self.current_intent)
        
        prompt, self.context = check_required_params(self.current_intent, self.attributes, self.context)

        #prompt being None means all parameters satisfied, perform the intent action
        if prompt is None:
            if self.context.name!='IntentComplete':
                prompt, self.context = check_actions(self.current_intent, self.attributes, self.context)
        
        #Resets the state after the Intent is complete
        if self.context.name=='IntentComplete':
            self.attributes = {}
            self.context = FirstGreeting()
            self.current_intent = None  
        
        return prompt

session = Session()  

class ChatbotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Chatbot")

        # Load the background image
        bg_image = ImageTk.PhotoImage(Image.open("background.png")) 

        # Create a label widget to display the background image
        bg_label = tk.Label(master, image=bg_image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Create the input label and text widget
        self.input_label = tk.Label(master, text="Enter your message:")
        self.input_label.pack()

        self.input_entry = tk.Entry(master, width=150)
        self.input_entry.pack()

        # Create the output label and text widget
        self.output_label = tk.Label(master, text="Bot response:")
        self.output_label.pack()

        self.output_text = tk.Text(master, height=30, width=400)
        self.output_text.pack()

        self.output_text.insert(tk.END, "Bot: Welcome to Tunisian Hotel Recommender Bot. How may I assist you?\n\n")

        # Create the submit and quit buttons
        self.submit_button = tk.Button(master, text="Submit", command=self.submit)
        self.submit_button.pack()

        self.quit_button = tk.Button(master, text="Quit", command=master.quit)
        self.quit_button.pack()

        self.session = session

    def submit(self):
        user_input = self.input_entry.get()
        self.input_entry.delete(0, tk.END)

        response = self.session.reply(user_input)

        self.output_text.insert(tk.END, "You: " + user_input + "\n")
        self.output_text.insert(tk.END, "Bot: " + response + "\n\n")
root = tk.Tk()
my_gui = ChatbotGUI(root)
root.mainloop()

