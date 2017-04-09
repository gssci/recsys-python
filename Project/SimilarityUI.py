import numpy as np
import pandas as pd
from sklearn import preprocessing
import random
from scipy.spatial import distance as d

#utility di sklearn che codifica attributi in forma di stringa, la usiamo per convertire le nazioni in numeri in modo coerente e confrontabile
le = preprocessing.LabelEncoder()

user_profiles = pd.read_csv("user_profile.csv", delimiter='\t')
target_users = pd.read_csv("target_users.csv", delimiter='\t')
item_profiles = pd.read_csv("item_profile.csv", delimiter='\t')

#set da cui dopo recupero gli user_id e l'id degli items, ristretti agli items attivi e ai target users
users_r = pd.merge(user_profiles,target_users,on='user_id')
items_r = item_profiles[item_profiles['active_during_test'] == 1].reset_index().drop('index',1)

#lista degli attributi in comune tra utenti e items, ovviamente confronto users e items solo su quelli
common_attributes = np.intersect1d(item_profiles.columns.values,user_profiles.columns.values).tolist()
users = users_r[common_attributes]
items = items_r[common_attributes]

#rimuovo i valori nulli e li sostituisco con 0
users = users.fillna(0)
items = items.fillna(0)

# users['country'] = users['country'].replace(0,'null')
# users['country'] = le.fit_transform(users['country'])
#
# items['country'] = items['country'].replace(0,'null')
# items['country'] = le.fit_transform(items['country'])

#riporto tutte le colonne a int per togliere orrrendi float
items = items.astype(int)
users = users.astype(int)

def encode_feature(dataframe, to_encode):
    #utility di sklearn che ritorna la codifica 1-of-K di un attributo
    hot = preprocessing.OneHotEncoder(dtype='int')

    for feature in to_encode:
        a = hot.fit_transform(dataframe[feature].values.reshape((-1,1))).toarray()
        for i in range(np.shape(a)[1]):
            dataframe[feature + str(i)] = a[:,i]
    return

#to_encode = ['discipline_id', 'industry_id']
to_encode = common_attributes
encode_feature(items,to_encode)
encode_feature(users,to_encode)
items = items.drop(to_encode,1)
users = users.drop(to_encode,1)

#aggiungi colonne con valori zero che sono presenti in users ma non in items (per esempio c'è un industry_id in user che è 23 ma in items è al massimo 21 quindi mancano due colonne)
#le aggiungo e le metto a zero per rendere i due vettori confrontabili
for attribute in users.columns.difference(items.columns).tolist():
    items[attribute] = np.zeros(items[[0]].shape)

items = items.astype(int).sort_index(axis=1)
users = users.astype(int).sort_index(axis=1)

# cm = np.intersect1d(items.columns.values,users.columns.values).tolist()
# items = items[cm]
# users = users[cm]

def similarity(u,v):
    C = 5
    a = np.dot(u,v)
    b = np.dot(np.linalg.norm(u),np.linalg.norm(v)) + C
    return a/b

interactions = pd.read_csv('interactions.csv', delimiter="\t")

def similarity_matrix():
    users_by_id = users_r['user_id'].values
    users_by_index = users.as_matrix()
    items_by_index = items.as_matrix()
    similarities_per_user = np.zeros((10000,63446))

    for u in range(10000):
        user_id = users_by_id[u]
        user = users_by_index[u]

        #escludi items con cui l'utente u ha già interagito
        interacted = interactions[interactions['user_id'] == user_id]['item_id'].values
        bad_indices = items_r[items_r.id.isin(interacted)].index.tolist()
        raccomandabili = items[~items.index.isin(bad_indices)]

        print(str(u))
        for i in raccomandabili.index.tolist():
            item = items_by_index[i]
            similarities_per_user[u][i] = similarity(user,item)

    return similarities_per_user


def extract_reccomendations(similarity_matrix):
    suggestions = np.zeros((10000,))
    items_by_id = items_r['id'].values

    for u in range(np.shape(similarity_matrix)[0]):
        indices = similarity_matrix[u].argsort()[-5:][::-1]
        suggestions[u] = [items_by_id[i] for i in indices]

    result = np.column_stack((users_r['user_id'].values,suggestions))
    result = result[result[:,0].argsort()] #comando speciale che mette una matrice in ordine rispetto soltanto una colonna, in questo caso gli id

    return result

from project_utils import output



