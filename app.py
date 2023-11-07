import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import Flask, request, render_template, jsonify, redirect, url_for
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

# menghubungkan file agar app.py dapat mengakses variable di file .env
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = 'mongodb://rkhawariz:merzy@ac-ds5pieh-shard-00-00.hweccjp.mongodb.net:27017,ac-ds5pieh-shard-00-01.hweccjp.mongodb.net:27017,ac-ds5pieh-shard-00-02.hweccjp.mongodb.net:27017/?ssl=true&replicaSet=atlas-h8931u-shard-0&authSource=admin&retryWrites=true&w=majority'
DB_NAME =  'dbsparta'

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    # perulangan untuk menyortir data yang akan ditampung pada variable word. dari database
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type (definition) is str else definition[0]
        # memasangkan key dengan nama word baru dengan key word yang ada pada words_result(yang sudah ditampung pada variable word)
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get("msg")
    return render_template('index.html', words=words, msg=msg)

@app.route('/detail/<keyword>')
def detail(keyword):
        api_key = '82eb05f4-2cb3-4a8a-8c0b-ded9f69cf20d'
        url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
        response = requests.get(url)
        definitions = response.json()
        # jika server tidak merespon apapun pada kata yang input user, arahkan ke halaman error dengan pesan berikut
        if not definitions:
            return redirect(url_for(
                'error',
                msg1 = f'Your word "{keyword}", could not be found',
                msg2 = 'nothing'
            ))
        # jika respon server pada index pertama adalah string(bukan array ataupun objek), tampung respon ke dalam variable, gabungkaan dengan tanda koma dan spasi. lalu lemparkan data ke /error
        if type(definitions[0]) is str:
            suggestions = ', '.join(definitions)
            return redirect(url_for(
                'error',
                msg1 = f'Your word "{keyword}", could not be found.',
                msg2 = 'Here are some suggested words:',
                suggestions = suggestions
            ))
        status = request.args.get('status_give', 'new')
        return render_template(
            'detail.html',
            word=keyword,
            definitions=definitions,
            status=status
            )

@app.route('/error')
def error():
    msg1= request.args.get('msg1')
    msg2= request.args.get('msg2')
    items = request.args.get('suggestions', '').split(',')
    # key items di bawah nantinya akan dipanggil di error.html menggunakan Jinja2
    return render_template('error.html', msg1=msg1, msg2=msg2, items=items)

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y%m%d'),
    }
    
    db.words.insert_one(doc)
    return jsonify ({
        'result': 'success',
        'msg': f'the word {word}, was saved!',
    })
    
@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify ({
        'result': 'success',
        'msg': f'the word {word}, was deleted!',
    })
   
@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word':word})
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id' : str(example.get('_id'))
        })
    return jsonify({
        'result' : 'success',
        'examples' : examples
    })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word' : word,
        'example' : example
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result' : 'success',
        'msg' : f'Your example, {example}, for the word, {word} was saved!'
    })

@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id' : ObjectId(id)})
    return jsonify({
        'result' : 'success',
        'msg' : f'Your example for the word, {word}, was deleted!'
    })

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)