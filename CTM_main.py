#!/usr/bin/env python
# coding: utf-8

# CTM Mapping module using JSON Object as a configuration file
# Author: Ahmed Elhossiny
#Version: 1.0
#Date: 2020-07-27
import pandas as pd
import sys
#import numpy as np
from datetime import datetime
import json

#This is my comment
#Convert Date Column from Exisitng Formart to Desired OutReport Format
def convertDateFormat(Column,old_format):
    Column=Column.apply(lambda x: datetime.strftime(datetime.strptime(x, old_format),'%Y%m%d'))
    return Column


#Execute Expression from Json Config file
def executeExpression (expression):
    outputColumn=eval(expression)
    return outputColumn

# Execurte Function from Json Config File
def executeFunction (expression):
    eval(expression)


#Generate Opening Balance Column based on beginning day balance
def openingBalancePerDay(attributeName,balanceColumn):
    global df
    global linesDf
    global Output
    global firstRecordIndex
    dateSet=set(linesDf['updatedDate'])
    for date in dateSet:
        Output.loc[Output.StatementDate==date,attributeName]=float(df.at[linesDf.index[linesDf.updatedDate==date][0]+firstRecordIndex-1,balanceColumn])
    return


#Generate Closing Balance Column based on closing day balance
def closingBalancePerDay(attributeName,balanceColumn):
    global df
    global linesDf
    global Output
    global firstRecordIndex
    dateSet=set(linesDf['updatedDate'])
    for date in dateSet:
        Output.loc[Output.StatementDate==date,attributeName]=float(linesDf.at[linesDf.index[linesDf.updatedDate==date][-1],balanceColumn])
    return
    

#Open and Load Json file
json_data = open(str(sys.argv[2]),encoding="utf8")
jsonFile = json.load(json_data)
json_data.close()

#Read Bank Statement
df=pd.read_excel(str(sys.argv[3]))

#Format DF columns
df.columns=list(jsonFile['Header'])


#Getting index of first and last row in Tabular section
lastRecordIndex=df.index[~df[jsonFile['recordIndexColumn']].isna()][-1]

firstRecordIndex=df.index[df[jsonFile['recordIndexColumn']]==jsonFile['recordIndexValue']][0]

if jsonFile['recordIndexHeader']=='Y':
    firstRecordIndex+=1

#Generate new Dataset for Tabular section
linesDf=df.iloc[firstRecordIndex:lastRecordIndex+1].reset_index(drop=True)

#Transform date column
linesDf['updatedDate']= executeExpression(jsonFile['updatedDate']['mappingStatement'])

if jsonFile['updatedDate']['dateFormat']!='OK':
    linesDf['updatedDate']=convertDateFormat(linesDf['updatedDate'],jsonFile['updatedDate']['dateFormat'])

#Generate empty Dataframe for output
Output=pd.DataFrame()

#Transform and Generate Output Columns
for x in jsonFile['outputColumns']:
    if jsonFile['outputColumns'][x]['initialCreation']=='Y':
        Output[x]=None
    if jsonFile['outputColumns'][x]['mappingType']=='Expression':
        Output[x]= executeExpression(jsonFile['outputColumns'][x]['mappingStatement'])
    elif jsonFile['outputColumns'][x]['mappingType']=='Fixed':
        Output[x]=jsonFile['outputColumns'][x]['mappingStatement']
    elif jsonFile['outputColumns'][x]['mappingType']=='Function':
        executeFunction(jsonFile['outputColumns'][x]['mappingStatement'])
    else:
        Output[x]=None
    if (jsonFile['outputColumns'][x]['dataType']=='Date') and (jsonFile['updatedDate']['dateFormat']!='OK') :
        Output[x]=convertDateFormat(Output[x],jsonFile['outputColumns'][x]['dateFormat'])

#Sort output columns in order
columns=['CashManagementAccount','Intraday','StatementDate','Currency','StatementOpeningLedger','StatementClosingLedger','StatementOpeningAvailable','StatementClosingAvailable','ValueDate','BankTransactionTypeCode','DebitCreditIndicator','LineAmount','BankReferenceNumber','RelatedReference','TextReferenceNumber','Description']

Output=Output[columns]

#Generate output CSV file
Output.to_csv(str(sys.argv[4]),index=False)
