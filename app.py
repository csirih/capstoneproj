import datetime
import jwt
from flask import Flask, jsonify
import subprocess
from flask import request, make_response
import re
from llama_index.core import SummaryIndex
from llama_index.readers.web import SimpleWebPageReader
from fastembed import TextEmbedding
from llama_index.readers.web import SimpleWebPageReader

from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from dotenv import load_dotenv
from llama_index.embeddings.openai import  OpenAIEmbedding
import os
from functools import wraps
embedding_model = TextEmbedding("BAAI/bge-base-en-v1.5")
app =Flask(__name__)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        BASEDIR = os.path.abspath(os.path.dirname(__file__))
        load_dotenv(os.path.join(BASEDIR, '.env'))
        secret = os.getenv("SECRET_KEY")
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'token is missing'})
        try:
            data = jwt.decode(token, secret,algorithms='HS256')
        except Exception as e:

            return jsonify({'message': 'Token is invalid'})
        return f(*args, **kwargs)
    return decorated

@app.route('/chat', methods =['POST'])
@token_required
def get_contextdata():
  data=request.json['messages']
  filtered =[message for message in data if message['role'] == "user"]
  url =getUrl(filtered[0]['content'])
  prompt= getPrompt(filtered[0]['content'])
  engine= createIndex(url)
  response= engine.query(prompt)
  responseStr = "{" + '"answer"' + ":" + response.response + "}"
  return responseStr


def getUrl(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return url[0][0]

def getPrompt(string):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    prompt = url_pattern.sub('', string)
    return prompt
def createIndex(string):
    storage_context = StorageContext.from_defaults()
    read_storage_context = StorageContext.from_defaults(persist_dir="./storage")
    index_id = string
    try:
      index = load_index_from_storage(read_storage_context,index_id)
    except:
      BASEDIR = os.path.abspath(os.path.dirname(__file__))
      load_dotenv(os.path.join(BASEDIR, '.env'))
      os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
      Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1, api_key=os.getenv("OPENAI_API_KEY"))
      Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", embed_batch_size=100)
      documents = SimpleWebPageReader(html_to_text=True).load_data([string])
      index = VectorStoreIndex.from_documents(documents,storage_context=storage_context,show_progress=True)
      index.set_index_id(string)
      index.storage_context.persist()
    query_engine = index.as_query_engine(similarity_top_k=15, verbose=True)
    return query_engine

@app.route('/login' , methods =['POST'])
def login():
    auth = request.json
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, '.env'))
    secret = os.getenv("SECRET_KEY")
    pwd = os.getenv("PWD")
    if auth and auth['password'] == pwd:
        token = jwt.encode({'user' : auth['username'], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=20)},secret)
        return jsonify({'token': token})
    return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm = login request'})



