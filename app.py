from flask import Flask, request,render_template
from flask import jsonify
import requests
import re
from bs4 import BeautifulSoup
from transformers import BertTokenizer
from transformers import BertForSequenceClassification
import torch
import pandas as pd
#column_names = ["News", "Sentiment"]



tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('pytorch_model.bin',config='config.json',num_labels=3)
label_list=['Positive','Negative','Neutral']
stringtoadd = '<thead><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous"></head><body><table border="1" class="dataframe" style="background: linear-gradient(45deg, #bb930047, transparent);"><tr style="text-align: right;"><th></th><th class="text-center">News</th><th>Sentiment</th></tr></thead> '
def format_color_groups(values):
    if values =='Negative':
        return  'color:red;border-collapse: collapse; border: 1px solid black;'
    elif values  == 'Positive':
        return  'color:green;border-collapse: collapse; border: 1px solid black;'
    else:
        return  'border-collapse: collapse; border: 1px solid black;'
def highlight(s):
    if s == 'Positive':
        return ['background-color: green']
    if s == 'Negative':
        return ['background-color: red']  
def highlight_greaterthan(s, threshold, column):
    is_max = pd.Series(data=False, index=s.index)
    is_max[column] = s.loc[column] == threshold
    return ['background-color: #90EE90' if is_max.any() else 'background-color: #ffcccb' for v in is_max]



def color_negative_red(x):
    c1 = 'background-color: red'
    c2 = 'background-color: black'

    df1 = pd.DataFrame(c2, index=x.index, columns=x.columns)
    df1 = df1.where((x == 'negative').all(axis=1), c1)
    df1 = df1.where((x == 'positive').all(axis=1), c1)    
    return df1
def set_header_font():
    return [dict(selector="th",
                 props=[("font-size", "15pt"),("font-family", 'Cambria')])]


def sent(strr):
    inputs = tokenizer(strr, return_tensors="pt")
    outputs = model(**inputs)
    out = label_list[torch.argmax(outputs[0])]
    return out
  
def search_sentiment(string):
    df = pd.DataFrame()
    
    qury = string
    qury = qury.replace(" ", "+")
    URL = f"https://news.google.com/search?q={qury}"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    xxx = soup.find_all("a")
    res = soup.get_text()

    resss = res
    for i in range(len(res)-1):
        #if (resss[i].islower() or resss[i].isdigit()) and (resss[i+1].isupper()) :
        if (resss[i].islower()) and (resss[i+1].isupper()) :    
            resss = resss[:i+1] + "   " + resss[i+1:]
    resss = resss[resss.find('About Google   ')+15:]        
    resss = resss.replace(':','')
    #print(resss)       
    #resss = (re.sub('^.*?#', " ",resss))        

    ls = resss.split("   ")
    lsss = []

    orginalsent = []
    news = []
    dictmain = {}
    dicti = {}
    overall = "neutral"
    for i in ls:
        if (i.find("sharemore_vert") == -1) and (len(i.split()) >2):
            #print(len(i.split()))
            z = (sent(i))                        
            if z!="Neutral":
                dicti[i] = z
                lsss.append(z)
                news.append(i)
                orginalsent.append(z)                
    df["News"]  = pd.Series(news) 
    df["Sentiment"]  = pd.Series(orginalsent)  
    if lsss.count("Positive")> lsss.count("Negative"):
        overall = "Positive"
    if lsss.count("Positive")< lsss.count("Negative"):   
        overall = "Negative"    
       
    #print("positve count " + str(lsss.count("positive")))        
    #print("negative count " + str(lsss.count("negative")))   
    #print("neutral count " + str(lsss.count("neutral"))) 
    
    df.dropna() 
    df.index += 1
    

    global html

    
    #df = df.style.applymap(format_color_groups)
    #now df is styler so no need to add style
    #df = df.set_table_attributes('style="border-collapse: collapse; border: 1px solid black;"')
    #df = df.style.apply(highlight, axis=1)
    df = df.style.apply(highlight_greaterthan, threshold='Positive', column=['Sentiment'], axis=1).set_properties(**{    'font-size': '15pt',} ).set_table_styles(set_header_font())
    #html = df.to_html()
    html = df
    return {"sentiment":dicti,"count":{"Positve":lsss.count("Positve"),"Negative":lsss.count("Negative")},"overall_sentiment":overall}
    
app = Flask(__name__,template_folder = 'templates')
@app.route('/')
def home():

    return render_template('index.html')

@app.route('/predict',methods=['POST'])
def predict():
    ADR = (request.form.get('ADR'))

    result  = (search_sentiment(ADR))
    
    #search_sentiment(args1)

    #return jsonify(result)
    #return render_template("index.html")
    #return render_template(html)
    print(html)
    #htmledit = html[html.find('</thead>')+ len('</thead>'):]
    #htmledit = stringtoadd+htmledit
    
    
    return (html.render())    
@app.route('/parameters', methods=['GET'])
def query_strings():
    args1 = request.args['query']

    result  = str(search_sentiment(args1))

    return result  
 
#http://127.0.0.1:5000/parameters?query=tata%20power
if __name__ == '__main__':
    app.run(port = 9045)