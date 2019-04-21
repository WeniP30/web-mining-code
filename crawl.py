"""
Created on Thu Apr 11 20:42:47 2019
@author: WeniPS
"""

from requests import get
from bs4 import BeautifulSoup
import sqlite3
import csv
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from math import log10
import numpy as np
from sklearn.metrics import silhouette_samples, silhouette_score
import skfuzzy as fuzz
#==crawling website
judul=[]
developer=[]
deskripsi=[]
urls=[str(i) for i in range (1,10)]
for url in urls :
    page=get("https://www.dicoding.com/events?q=&criteria=&sort=&sort_direction=desc&page="+url)
    soup=BeautifulSoup(page.content,'html.parser')
    jdl=soup.findAll(class_='item-box-name')
    dev=soup.findAll('div',attrs={'class':'item-box-main-information'})
    desk=soup.findAll('div',attrs={'class':'item-box-main-information'})
    for a in range (len(jdl)):
        judul+=[jdl[a].getText()]
    for b in range (len(dev)):
        developer+=[dev[b].find('p').text]
    for c in range(len(desk)):
        deskripsi+=[desk[c].find_all('p')[1].text]
        
#==create & insert ke db
conn = sqlite3.connect('events.db')
conn.execute('''CREATE TABLE if not exists EVENTS
         (NAMA_EVENT VARCHAR NOT NULL,
         DEVELOPER VARCHAR NOT NULL,
         DESKRIPSI VARCHAR NOT NULL);''')
for i in range (len(judul)):
    conn.execute('INSERT INTO EVENTS(NAMA_EVENT,DEVELOPER,DESKRIPSI) values (?, ?, ?)', (judul[i], developer[i], deskripsi[i]))

#==menampilkan data dari db
conn.commit()
cursor = conn.execute("SELECT* from EVENTS")
for row in cursor:
    print(row)

#==ambil kata dasar dr deskripsi
factory = StopWordRemoverFactory()
stopword = factory.create_stop_word_remover ()

factorym = StemmerFactory ()
stemmer = factorym.create_stemmer ()

tmp = ''
for i in deskripsi:
    tmp = tmp + ' ' +i

hasil = []
for i in tmp.split():
    try :
        if i.isalpha() and (not i in hasil) and len(i)>2:
            # Menghilangkan Kata tidak penting
            stop = stopword.remove(i)
            if stop != "":
                out = stemmer.stem(stop)
                hasil.append(out)
    except:
        continue
katadasar=hasil
print("kata dasar :\n",katadasar)

#==saring kata dasar ke KBI
conn = sqlite3.connect('KBI.db')
cur_kbi = conn.execute("SELECT* from KATA")
def LinearSearch (kbi,kata):
    found=False
    posisi=0
    while posisi < len (kata) and not found :
        if kata[posisi]==kbi:
            found=True
        posisi=posisi+1
    return found
#-----kata yg sesuai KBI
berhasil=[]
berhasil2=''
for kata in cur_kbi :
    ketemu=LinearSearch(kata[0],katadasar)
    if ketemu :
        kata = kata[0]
        berhasil.append(kata)
        berhasil2=berhasil2+' '+kata
print('kata sesuai KBI :',berhasil)
#------VSM kata KBI
conn = sqlite3.connect('events.db')
matrix=[]
cursor = conn.execute("SELECT* from EVENTS")
for row in cursor:
    tampung = []
    for i in berhasil:
        tampung.append(row[2].lower().count(i))
    matrix.append(tampung)
#------CSV hasil VSM KBI
with open('VSMkbi.csv', mode='w') as employee_file:
    employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    employee_writer.writerow(berhasil)
    for i in matrix:
        employee_writer.writerow(i)

#==TF-IDF
df = list()
for d in range (len(matrix[0])):
    total = 0
    for i in range(len(matrix)):
        if matrix[i][d] !=0:
            total += 1
    df.append(total)

idf = list()
for i in df:
    tmp = 1 + log10(len(matrix)/(1+i))
    idf.append(tmp)

tf = matrix
tfidf = []
for baris in range(len(matrix)):
    tampungBaris = []
    for kolom in range(len(matrix[0])):
        tmp = tf[baris][kolom] * idf[kolom]
        tampungBaris.append(tmp)
    tfidf.append(tampungBaris)
#------CSV hasil TF-IDF
with open('TFIDF.csv', mode='w') as employee_file:
    employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    employee_writer.writerow(berhasil)
    for i in tfidf:
        employee_writer.writerow(i)
        
#==Seleksi Fitur - Pearson
def pearsonCalculate(data, u,v):
    "i, j is an index"
    atas=0; bawah_kiri=0; bawah_kanan = 0
    for k in range(len(data)):
        atas += (data[k,u] - meanFitur[u]) * (data[k,v] - meanFitur[v])
        bawah_kiri += (data[k,u] - meanFitur[u])**2
        bawah_kanan += (data[k,v] - meanFitur[v])**2
    bawah_kiri = bawah_kiri ** 0.5
    bawah_kanan = bawah_kanan ** 0.5
    return (atas/(bawah_kiri * bawah_kanan))
def meanF(data):
    meanFitur=[]
    for i in range(len(data[0])):
        meanFitur.append(sum(data[:,i])/len(data))
    return np.array(meanFitur)
def seleksiFiturPearson(data, threshold, berhasil):
    global meanFitur
    data = np.array(data)
    meanFitur = meanF(data)
    u=0
    while u < len(data[0]):
        dataBaru=data[:, :u+1]
        meanBaru=meanFitur[:u+1]
        seleksikata=berhasil[:u+1]
        v = u
        while v < len(data[0]):
            if u != v:
                value = pearsonCalculate(data, u,v)
                if value < threshold:
                    dataBaru = np.hstack((dataBaru, data[:, v].reshape(data.shape[0],1)))
                    meanBaru = np.hstack((meanBaru, meanFitur[v]))
                    seleksikata = np.hstack((seleksikata, berhasil[v]))
            v+=1
        data = dataBaru
        meanFitur=meanBaru
        berhasil=seleksikata
        if u%50 == 0 : print("proses : ", u, data.shape)
        u+=1
    return data, seleksikata

xBaru2,kataBaru = seleksiFiturPearson(tfidf, 0.9, berhasil)
xBaru1,kataBaru2 = seleksiFiturPearson(xBaru2, 0.8, berhasil)
#------CSV Seleksi Fitur
with open('Fitur.csv', mode='w') as employee_file:
    employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    employee_writer.writerow(kataBaru2)
    #employee_writer.writerow()

#==Clustering
print("Cluster dgn Seleksi Fitur : 0.8")
cntr, u, u0, distant, fObj, iterasi, fpc =  fuzz.cmeans(xBaru1.T, 3, 2, 0.00001, 1000, seed=0)
membership = np.argmax(u, axis=0)

silhouette = silhouette_samples(xBaru1, membership)
s_avg = silhouette_score(xBaru1, membership, random_state=10)

for i in range(len(tfidf)):
    print("c "+str(membership[i]))#+"\t" + str(silhouette[i]))
print(s_avg)
#------CSV Clustering
def write_csv(nama_file, isi, tipe='w'):
    'tipe=w; write; tipe=a; append;'
    with open(nama_file, mode=tipe) as tbl:
        tbl_writer = csv.writer(tbl, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in isi:
            tbl_writer.writerow(row)
write_csv("Cluster.csv", [["Cluster"]])
write_csv("Cluster.csv", [membership],        "a")
write_csv("Cluster.csv", [["silhouette"]],    "a")
write_csv("Cluster.csv", [silhouette],        "a")
write_csv("Cluster.csv", [["Keanggotaan"]],   "a")
write_csv("Cluster.csv", u,                   "a")
write_csv("Cluster.csv", [["pusat Cluster"]], "a")
write_csv("Cluster.csv", cntr,                "a")