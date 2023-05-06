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

def input_processor(user_input, context, attributes, current_intent):
    '''This function marks the entities in user input, and updates the attributes dictionary'''
    # Can use context to context specific attribute fetching
    if context.name == 'IntentComplete':
        return attributes, user_input
    else:
        # Code can be optimised here, loading the same files each time suboptimal
        files = os.listdir('./entities/')
        entities = {}
        for fil in files:
            if fil != '.ipynb_checkpoints':
                lines = open('./entities/' + fil).readlines()
                for i, line in enumerate(lines):
                    lines[i] = line[:-1]
                entities[fil[:-4]] = '|'.join(lines)

        # Extract entity and update it in attributes dict
        for entity in entities:
            for i in entities[entity].split('|'):
                if i.lower() in user_input.lower():
                    attributes[entity] = i
        for entity in entities:
            user_input = re.sub(entities[entity], r'$' + entity, user_input, flags=re.IGNORECASE)

        return attributes, user_input


def intentIdentifier(user_input, context, current_intent):
    '''This function identifies the user intent'''
    intent = None
    
    if context.name == 'FirstGreeting':
        intent = FirstGreeting()
    elif context.name == 'IntentComplete':
        intent = IntentComplete()
    elif context.name == 'ValidateLocation':
        intent = ValidateLocation()
    elif context.name == 'ValidateCuisine':
        intent = ValidateCuisine()
    elif context.name == 'ValidateCostType':
        intent = ValidateCostType()
    elif context.name == 'ValidateHotelClass':
        intent = ValidateHotelClass()
    elif context.name == 'ValidateNights':
        intent = ValidateNights()
    elif context.name == 'ValidateCheckinDate':
        intent = ValidateCheckinDate()
    else:
        if current_intent:
            intent = current_intent
        else:
            intent = IntentComplete()

    return intent


def check_required_params(intent, attributes, context):
    '''This function checks if the required parameters for an intent are present'''
    prompt = None

    if intent.name == 'BookRestaurant':
        if 'neighbourhood' not in attributes:
            prompt = "Which neighbourhood do you want the restaurant to be in?"
            context.active = True
            context.name = 'ValidateLocation'
        elif 'cusine' not in attributes:
            prompt = "What type of cuisine are you looking for?"
            context.active = True
            context.name = 'ValidateCuisine'
        elif 'costtype' not in attributes:
            prompt = "What is your preferred cost type?"
            context.active = True
            context.name = 'ValidateCostType'
    elif intent.name == 'bookinghotel':
        if 'location' not in attributes:
            prompt = "Which location do you want to book a hotel in?"
            context.active = True
            context.name = 'ValidateLocation'
        elif 'roomtariffplan' not in attributes:
            prompt = "What type of room tariff plan do you prefer?"
            context.active = True
            context.name = 'ValidateCostType'
        elif 'hotelclass' not in attributes:
            prompt = "What is your preferred hotel class?"
            context.active = True
            context.name = 'ValidateHotelClass'
        elif 'nights' not in attributes:
            prompt = "How many nights do you want to stay?"
            context.active = True
            context.name = 'ValidateNights'
        elif 'checkin' not in attributes:
            prompt = "On what date do you want to check in? Please enter in dd/mm/yyyy format."
            context.active = True
            context.name = 'ValidateCheckinDate'

    return prompt, context


def check_actions(intent, attributes, context):
    '''This function performs the actions for an intent'''
    prompt = None
    
    if intent.name == 'BookRestaurant':
        df = pd.read_csv('data/restaurants.csv')
        df = df.drop('Address', axis=1)
        cuisinecondition = df['cusine'].str.lower() == attributes['cusine'].lower()
        locationcondition = df['neighbourhood'].str.lower() == attributes['neighbourhood'].lower()
        costtypecondition = df['costtype'].str.lower() == attributes['costtype'].lower()
        df = df[cuisinecondition & locationcondition & costtypecondition]
        if not df.empty:
            prompt = df.to_string(index=False)
        else:
            prompt = "Sorry, no restaurants found with the given information. Please try again."
        context.active = False
        context.name = 'IntentComplete'
    elif intent.name == 'bookinghotel':
        df = pd.read_csv('data/hotels.csv')
        df = df.drop('nights', axis=1)
        locationcondition = df['location'].str.lower() == attributes['location'].lower()
        roomtariffplancondition = df['roomtariffplan'].str.lower() == attributes['roomtariffplan'].lower()
        hotelclasscondition = df['hotelclass'].str.lower() == attributes['hotelclass'].lower()
        df = df[locationcondition & roomtariffplancondition & hotelclasscondition]
        if not df.empty:
            prompt = df.to_string(index=False)
        else:
            prompt = "Sorry, no hotels found with the given information. Please try again."
        context.active = False
        context.name = 'IntentComplete'

    return prompt, context


class Session:
    def __init__(self, attributes=None, active_contexts=[FirstGreeting(), IntentComplete()]):
        '''Initialise a default session'''
        # Active contexts not used yet, can use it to have multiple contexts
        self.active_contexts = active_contexts
        # Contexts are flags which control dialogue flow, see Contexts.py
        self.context = FirstGreeting()
        # Intent tracks the current state of dialogue
        self.current_intent = None
        # Attributes hold the information collected over the conversation
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
        # prompt being None means all parameters satisfied, perform the intent action
        if prompt is None:
            if self.context.name != 'IntentComplete':
                prompt, self.context = check_actions(self.current_intent, self.attributes, self.context)
        # Resets the state after the Intent is complete
        if self.context.name == 'IntentComplete':
            self.attributes = {}
            self.context = FirstGreeting()
            self.current_intent = None
        self.update_contexts()
        return prompt
session = Session()  

#!/usr/bin/python
# -*- coding: utf-8 -*-


class ChatbotGUI:

    def __init__(self, master):
        self.master = master
        master.title('Chatbot')

        self.input_label = tk.Label(master, text='Enter your message:')
        self.input_label.pack()

        self.input_entry = tk.Entry(master, width=150)
        self.input_entry.pack()

        self.output_label = tk.Label(master, text='Bot response:')
        self.output_label.pack()

        self.output_text = tk.Text(master, height=30, width=400)
        self.output_text.pack()

        self.output_text.insert(tk.END,
                                '''Bot: Welcome to Tunisian Hotel Recommender Bot. How may I assist you?

''')

        self.submit_button = tk.Button(master, text='Submit',
                command=self.submit)
        self.submit_button.pack()

        self.quit_button = tk.Button(master, text='Quit',
                command=master.quit)
        self.quit_button.pack()

        self.session = session

    def submit(self):
        user_input = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)
        self.output_text.insert(tk.END, 'You: ' + user_input + '\n')
        response = self.session.reply(user_input)
        if response is not None:
            self.output_text.insert(tk.END, 'Bot: ' + response
                                    + '''

''')


root = tk.Tk()
my_gui = ChatbotGUI(root)
root.mainloop()
