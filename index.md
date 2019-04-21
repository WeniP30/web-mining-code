## Pengantar

WENI PRATIWI S 160411100013

> using Anaconda

Web mining atau penambangan web merupakan proses ekstraksi pola dari data-data pada suatu website. Terdiridari 3 bagian yaitu :

1. Web content mining
2. Web structure mining
3. Web usage mining

Web content mining adalah proses ekstraksi pola/informasi dari dokumen atau data. Cara kerjanya adalah dengan cara mengekstraksi *key word* dari data, bisa berupa teks, citra, audio, video, metadata dan hyperlink.

**website :** "https://www.dicoding.com/events?q=&criteria=&sort=&sort_direction=desc&page=?"

**data :** 10 pages (11 event/page) atau 110 event/data

## *Crawling*

------

> using BeautifulSoup

```python
from requests import get
from bs4 import BeautifulSoup
```

Proses pertama adalah melakukan scan/crawl pada halaman web, dan mengambil data yang diinginkan.

*<u>Proses crawl :</u>*

```python
judul=[]
developer=[]
deskripsi=[]
urls=[str(i) for i in range (1,11)]
```

Buat list untuk menampung masing-masing data yang kita inginkan, list *urls* digunakan untuk menampung page/halaman (1-10).

```python
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
```

Kemudian kita lakukan crawl pada setiap halaman (1-10) dari website. *page* menampung link halaman , dimana *url* merupakan nomor halaman.

**contoh :**

page=get("https://www.dicoding.com/events?q=&criteria=&sort=&sort_direction=desc&page="+url)

urls=1 sampai 10

jika url = 1

page=get("https://www.dicoding.com/events?q=&criteria=&sort=&sort_direction=desc&page="+"1")

maka sistem akan mengakses halaman/page 1 dari website.

------

Mengambil informasi yang kita inginkan, lakukan *inspeksi elemen* dan ambil tag html dari data.

- data judul :

  ```
  <a class='item-box-name'>
  ```

- data developer :

  ```
  <div class='item-box-main-information'>
  ```

  pada tag 'p' pertama -->*.find('p')*

- data deskripsi :

  ```
  <div class='item-box-main-information'>
  ```

  pada tag 'p' kedua -->.find_all('p')[1]

Kemudian tambahkan setiap data pada list masing-masing.

*<u>Save data ke db :</u>*

Setelah berhasil mengambil data dari setiap halaman, kita tampung dalam db menggunakan sqlite.

```python
import sqlite3

conn = sqlite3.connect('events.db')
conn.execute('''CREATE TABLE if not exists EVENTS
         (NAMA_EVENT VARCHAR NOT NULL,
         DEVELOPER VARCHAR NOT NULL,
         DESKRIPSI VARCHAR NOT NULL);''')
for i in range (len(judul)):
    conn.execute('INSERT INTO EVENTS(NAMA_EVENT,DEVELOPER,DESKRIPSI) values (?, ?, ?)', (judul[i], developer[i], deskripsi[i]))
```

Code diatas digunakan untuk membuat db *events.db* dengan 3 kolom (judul,developer dan deskripsi), kemudian menampung setiap data dari list hasil crawl ke masing-masing kolom dari db.

## Pre-*Processing*

------

> using Sastrawi + KBI

```python
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
```

Data yang telah kita dapat perlu dilakukan pre-processing untuk mendapatkan *key word* yang akan menjadi sebuah fitur (kata penting).

1. Tokenizing - mengambil setiap kata dari kalimat

2. Stemming - mengambil kata baku dari hasil tokenizing

3. Filtering/remove - membuang kata yang termasuk kata penghubung

4. Penambahan kata pada list stopword untuk menghilangkan kata hubung/kata tidak penting.

   akses : Anaconda3\Lib\site-packages\Sastrawi\StopWordRemover\StopWordRemoverFactory.py

<u>*ekstraksi kata dasar :*</u> 

```python
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
```

Code diatas digunakan untuk mengekstaksi kata dasar, membuang fitur yang bukan berupa text dan fitur yang termasuk kata hubung menggunakan library dari sastrawi.

**contoh :**

kalimat input : "saya jalan2 membeli sayur di pasar"

kalimat output : "saya jalan beli sayur pasar"

------

<u>*cek kata dalam KBI :*</u>

```python
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
```

Dalam proses ini kita memerlukan database KBI untuk mengecek setiap kata yang sesuai/baku. Kemudian buat sebuah function *LinearSearch* untuk mengecek setiap kata pada *katadasar* yang sesuai dengan KBI, dengan return value *found* .

```python
berhasil=[]
for kata in cur_kbi :
    ketemu=LinearSearch(kata[0],katadasar)
    if ketemu :
        kata = kata[0]
        berhasil.append(kata)
```

- Jika *found=true* maka kata tersebut merupakan kata baku sesuai KBI, jadi kata tersebut kita simpan pada list *berhasil*. 
- Jika *found=false* maka kata tersebut bukan kata baku sesuai KBI, jadi kata tersebut tidak perlu disimpan.

## *VSM*

------

VSM merupakan proses menghitung frekuensi kemunculan setiap kata pada setiap data, dalam bentuk matriks.

data 1 : "telur ayam goreng"

data 2 : "masak telur goreng makan ayam goreng"

| data | ayam | goreng | masak | makan | telur |
| :--- | ---- | ------ | ----- | ----- | ----- |
| 1    | 1    | 1      | 0     | 0     | 1     |
| 2    | 1    | 2      | 1     | 1     | 1     |

```python
conn = sqlite3.connect('events.db')
matrix=[]
cursor = conn.execute("SELECT* from EVENTS")
for row in cursor:
    tampung = []
    for i in berhasil:
        tampung.append(row[2].lower().count(i))
    matrix.append(tampung)
```

code diatas akan mengecek dan menghitung berapa kali kata pada list *berhasil*  muncul pada setiap baris data dalam database *events.db*, kemudian menampung hasil frekuensi kemunculan dalam list *matrix*.

```python
import csv

with open('VSMkbi.csv', mode='w') as employee_file:
    employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    employee_writer.writerow(berhasil)
    for i in matrix:
        employee_writer.writerow(i)
```

kemudian simpan hasil dalam file csv, dengan kolom pertama berisi kata/fitur dan kolom selanjutnya berisi matriks.

## *TF-IDF*

------

TF-IDF merupakan kepanjangan dari Term Frequence dan Invers Document Frequence , dengan rumus TFxIDF. Maka kita memerlukan nilai TF dan nilai IDF. 

*<u>menghitung TF</u>*

TF sama dengan VSM yaitu menghitung frekuensi kemunculan kata pada setiap data.

*<u>menghitung IDF</u>*

pertama kita hitung DF (Document Frekuensi)

**contoh :**

data 1 : "telur ayam goreng"

data 2 : "masak telur goreng makan ayam goreng"

| kata   | jumlah data yang mengandung kata tersebut |
| ------ | ----------------------------------------- |
| ayam   | 2                                         |
| goreng | 2                                         |
| masak  | 1                                         |
| makan  | 1                                         |
| telur  | 2                                         |

```python
from math import log10

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
```

kemudian kita hitung TF x IDF

```
tf = matrix
tfidf = []
for baris in range(len(matrix)):
    tampungBaris = []
    for kolom in range(len(matrix[0])):
        tmp = tf[baris][kolom] * idf[kolom]
        tampungBaris.append(tmp)
    tfidf.append(tampungBaris)
```

hasil hitung akan ditampung pada list *tfidf*  , kemudian disimpan dalam bentuk csv  dengan kolom pertama berisi fitur.

```python
with open('TFIDF.csv', mode='w') as employee_file:
    employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    employee_writer.writerow(berhasil)
    for i in tfidf:
        employee_writer.writerow(i)
```

TF-IDF digunakan untuk mendapatkan bobot yang lebih akurat dibandingkan dengan hasil VSM.

## *Seleksi Fitur*

------

Proses seleksi fitur digunakan untuk mengurangi jumlah kata/fitur yang tidak penting, banyaknya fitur sangat berpengaruh pada hasil akhir clustering dan waktu untuk komputasi oleh karena itu seleksi fitur sangat dibutuhkan.

**pearson correlation**

Merupakan metode seleksi fitur sederhana dengan cara mengukur korelasi/hubungan setiap fitur, semakin tinggi nilai korelasi maka semakin kuat hubungan fiturnya.

```python
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
```



## *Clustering*

------

Clustering dilakukan untuk mengelompokkan  data dengan karakteristik yang sama ke suatu ‘class’ yang sama dan data dengan karakteristik yang berbeda ke ‘class’ yang lain.

Pada permasalahan ini digunakan fuzzy c-means, untuk mengelopokkan data menjadi 3 class. parameter dari fuzzy c-means : data, jumlah cluster, pembobot, eror maksimal dan iterasi maksimal.

```
cntr, u, u0, distant, fObj, iterasi, fpc =  fuzz.cmeans(xBaru1.T, 3, 2, 0.00001, 1000, seed=0)
membership = np.argmax(u, axis=0)

silhouette = silhouette_samples(xBaru1, membership)
s_avg = silhouette_score(xBaru1, membership, random_state=10)

for i in range(len(tfidf)):
    print("c "+str(membership[i]))
print(s_avg)
```

simpan hasil clustering 

```
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
```

