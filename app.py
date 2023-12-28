import copy
import re
import time
from collections import Counter
from random import random

from flask import Flask, render_template, request, jsonify
from sql_related import mysql_operator

app = Flask(__name__)
restored_cities_results, restored_reviews_results, distances = mysql_operator.get_data()

restored_scores = mysql_operator.get_score()


@app.route('/')
def mainp():
    return render_template('mainp.html')


@app.route('/q10')
def index10():
    return render_template('q10.html')


@app.route('/q11')
def index11():
    return render_template('q11.html')


@app.route('/q12')
def index12():
    return render_template('q12.html')


@app.route('/update_chart', methods=['POST'])
def update_chart():
    start_time = time.time()

    data = request.get_json()
    city = data.get('city')
    state = data.get('state')

    j = -1
    for i in range(0, len(restored_cities_results)):
        if restored_cities_results[i]['city'] == city and restored_cities_results[i]['state'] == state:
            j = i
            break

    if j == -1:
        return jsonify([])
    else:
        distance = distances[j]
        sorted_indices = sort_indices(distance)
        new_array = [[restored_cities_results[i]['city'], distances[j][i]] for i in sorted_indices]

        end_time = time.time()
        run_time = end_time - start_time

        return jsonify({"dis": new_array[1:], "t": run_time})


@app.route('/update_chart2', methods=['POST'])
def update_chart2():
    start_time = time.time()

    data = request.get_json()
    city = data.get('city')
    state = data.get('state')

    j = -1
    for i in range(0, len(restored_cities_results)):
        if restored_cities_results[i]['city'] == city and restored_cities_results[i]['state'] == state:
            j = i
            break

    if j == -1:
        return jsonify([])
    else:
        distance = distances[j]
        sorted_indices = sort_indices(distance)
        new_array = [[restored_cities_results[i]['city'], restored_scores[restored_cities_results[i]['city']]] for i in
                     sorted_indices]

        end_time = time.time()
        run_time = end_time - start_time

        return jsonify({"dis": new_array[1:], "t": run_time})


cityno_class = []
class_population = {}
class_citynumber = {}
class_reviewscore = {}
class_centercity = {}
class_mostpopulation = {}
class_allreview = {}


@app.route('/update_chart3', methods=['POST'])
def update_chart3():
    start_time = time.time()

    class_population.clear()
    class_citynumber.clear()
    class_reviewscore.clear()
    class_centercity.clear()
    class_mostpopulation.clear()
    class_allreview.clear()

    data = request.get_json()
    kid = data.get('kid')
    classid = data.get('classid')
    global cityno_class
    cityno_class = mysql_operator.knn_using(restored_cities_results, distances, kid, classid)

    for ls in cityno_class:
        if ls[1] in class_population:
            class_population[ls[1]] += int(restored_cities_results[ls[0]]['population'])

            class_citynumber[ls[1]] = class_citynumber[ls[1]] + 1
            class_reviewscore[ls[1]] += int(restored_reviews_results[ls[0]]['score']) * int(
                restored_cities_results[ls[0]]['population'])
            if int(restored_cities_results[ls[0]]['population']) > class_mostpopulation[ls[1]]:
                class_centercity[ls[1]] = [restored_reviews_results[ls[0]]['city'],
                                           restored_reviews_results[ls[0]]['state']]
                class_mostpopulation[ls[1]] = int(restored_cities_results[ls[0]]['population'])
            class_allreview[ls[1]] = class_allreview[ls[1]] + " " + restored_reviews_results[ls[0]]['review']

        else:
            # 否则，将类别添加到字典并初始化人口
            class_population[ls[1]] = int(restored_cities_results[ls[0]]['population'])

            class_citynumber[ls[1]] = 1
            class_reviewscore[ls[1]] = int(restored_reviews_results[ls[0]]['score']) * int(
                restored_cities_results[ls[0]]['population'])
            class_centercity[ls[1]] = [restored_cities_results[ls[0]]['city'], restored_cities_results[ls[0]]['state']]
            class_mostpopulation[ls[1]] = int(restored_cities_results[ls[0]]['population'])
            class_allreview[ls[1]] = restored_reviews_results[ls[0]]['review']

    result_array = sorted(class_population.items())
    end_time = time.time()
    run_time = end_time - start_time

    return jsonify({"re": result_array, "t": run_time})


@app.route('/update_chart4', methods=['POST'])
def update_chart4():

    data = request.get_json()
    ind = data.get('ind')
    ind = "class" + str(ind + 1)

    noc = class_citynumber[ind]
    was = float(class_reviewscore[ind]) / int(class_population[ind])
    cn, sn = class_centercity[ind][0], class_centercity[ind][1]
    labels = ["movie", "great", "time", "bought", "book", "love"]

    word_counts = {}
    for class_key, review in class_allreview.items():
        # 使用正则表达式将字符串分割成单词
        words = re.findall(r'\b\w+\b', review.lower())  # 转换为小写并使用正则表达式提取单词
        # 使用 Counter 统计每个单词的出现次数
        word_counts[class_key] = Counter(words)



    tm = 0
    tg = 0
    tt = 0
    tb = 0
    tbk = 0
    tl = 0
    for class_key, counts in word_counts.items():
        tm = tm + counts['movie']
        tg = tg + counts['great']
        tt = tt + counts['time']
        tb = tb + counts['bought']
        tbk = tbk + counts['book']
        tl = tl + counts['love']

    rad=[]
    rad.append(word_counts[ind]["movie"]/0.75/tm)
    rad.append(word_counts[ind]["great"] / 0.75 / tg)
    rad.append(word_counts[ind]["time"] / 0.75 / tt)
    rad.append(word_counts[ind]["bought"] / 0.75 / tb)
    rad.append(word_counts[ind]["book"] / 0.75 / tbk)
    rad.append(word_counts[ind]["love"] / 0.75 / tl)

    max = 0
    maxlabel = ''
    t=[tm,tg,tt,tb,tbk,tl]
    for i in range(0,len(labels)):
        if word_counts[ind][labels[i]]/0.75/t[i] > max:
            max = word_counts[ind][labels[i]]/0.75/t[i]
            maxlabel = labels[i]

    return jsonify({"noc": noc, "was": was, "cn": cn, "sn": sn, "sw":maxlabel,"labels": labels,"rad":rad})


def sort_indices(arr):
    return sorted(range(len(arr)), key=lambda k: arr[k])


if __name__ == '__main__':
    app.run(debug=True)
