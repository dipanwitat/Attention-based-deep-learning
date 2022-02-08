# -*- coding: utf-8 -*-
"""
Created on Tue Aug  3 20:20:03 2021

@author: Dipanwita
"""
from keras import Model
from keras.layers import Layer
import keras.backend as K
from keras.layers import Input, Dense, SimpleRNN
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from scipy import stats
import tensorflow as tf
import tensorflow.compat.v1 as v1
from sklearn.model_selection import LeaveOneOut
from keras.layers import Concatenate
from numpy import mean
from numpy import std
from numpy import dstack
from pandas import read_csv
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import TimeDistributed
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.utils import to_categorical
from matplotlib import pyplot
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, LSTM
from sklearn.metrics import plot_confusion_matrix
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Dropout
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.utils import to_categorical
import shap
import seaborn as sns
from pylab import rcParams
from sklearn import metrics
from sklearn.model_selection import train_test_split
sns.set(style='whitegrid', palette='muted', font_scale=1.5)
rcParams['figure.figsize'] = 14, 8
RANDOM_SEED = 42
import time
start_time = time.time()					#To keep track of time to run the code

print('Loading data ...')
		#Loading Accelerometer & Gyroscope data
data1 = pd.read_csv('D:/Research Program/phone_accelerometer.csv')
data2 = pd.read_csv('D:/Research Program/phone_gyroscope.csv')


length = len(data1)
data1 = data1.drop(labels = ['Arrival_Time','Creation_Time','Index', 'User'], axis=1)		#Dropping the unnecessary fields
data2 = data2.drop(labels = ['Arrival_Time','Creation_Time','Index', 'User','Model','Device'], axis=1)

data1 = data1.head(length)							#Taking only the top 'length' number of entries from both the data
data2 = data2.head(length)

data2.columns = ['x1', 'y1', 'z1', 'gt1']					#Renaming the column values of data2 as data1 would have same 'x','y' and 'z' variables

data = pd.concat([data1, data2], axis=1)			#Merging both the accelerometer and the gyroscope data			
to_drop = ['null']									#To drop the null values fro both data1 and data2
data = data[~data['gt'].isin(to_drop)]
data = data[~data['gt1'].isin(to_drop)]

data = data.drop(labels = ['gt1'], axis=1)
feature_input=pd.read_csv('D:/Research Program/feature_data.csv')

#check the null values 
print(data.isnull().sum())
if(data.isnull().sum().any() !=0):
    print("We have null values")
# making new data frame with dropped NA values
df = data.dropna(axis = 0, how ='any')
  
# comparing sizes of data frames
print("Old data frame length:", len(data), "\nNew data frame length:", 
       len(df), "\nNumber of rows with at least 1 NA value: ",
       (len(data)-len(df)))


N_TIME_STEPS = 128
N_FEATURES = 6
step = 20
segments = []
labels = []
acc_per_fold = []
loss_per_fold = []
for i in range(0, len(df) - N_TIME_STEPS, step):
    xa = df['x'].values[i: i + N_TIME_STEPS]
    ya = df['y'].values[i: i + N_TIME_STEPS]
    za = df['z'].values[i: i + N_TIME_STEPS]
    xg = df['x1'].values[i: i + N_TIME_STEPS]
    yg = df['y1'].values[i: i + N_TIME_STEPS]
    zg = df['z1'].values[i: i + N_TIME_STEPS]
    label = stats.mode(df['gt'][i: i + N_TIME_STEPS])[0][0]
    segments.append([xa, ya, za, xg, yg, zg])
    labels.append(label)
    
reshaped_segments = np.asarray(segments, dtype= np.float32).reshape(-1, N_TIME_STEPS, N_FEATURES)
labels = np.asarray(pd.get_dummies(labels), dtype = np.float32)
X_train, X_test, y_train, y_test = train_test_split(
        reshaped_segments, labels, test_size=0.2, random_state=RANDOM_SEED)
n_timesteps, n_features, n_outputs = X_train.shape[1], X_train.shape[2], y_train.shape[1]
# Define the K-fold Cross Validator
loso = LeaveOneOut()


for train, test in loso.split(reshaped_segments, labels):
    model = Sequential()
    model.add(TimeDistributed(Conv1D(filters=64, kernel_size=3, activation='relu'), input_shape=(None,32,6)))
    model.add(TimeDistributed(Conv1D(filters=64, kernel_size=3, activation='relu')))
    model.add(TimeDistributed(Dropout(0.5)))
    model.add(TimeDistributed(MaxPooling1D(pool_size=2)))
    model.add(TimeDistributed(Flatten()))
    model.add(LSTM(100))
    model.add(Dropout(0.5))
    model.add(Dense(100, activation='relu'))
    model.add(Dense(n_outputs, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    history_CNN = model.fit(reshaped_segments[train],
                    labels[train],
                    epochs=30,
                    batch_size=64,
                    verbose=1)
    # Generate generalization metrics
    scores = model.evaluate(reshaped_segments[test], labels[test], verbose=0)
    print('Score'': {model.metrics_names[0]} of {scores[0]}; {model.metrics_names[1]} of {scores[1]*100}%')
    acc_per_fold.append(scores[1] * 100)
    loss_per_fold.append(scores[0])

    
# == Provide average scores ==
print('------------------------------------------------------------------------')
print('Score per fold')
for i in range(0, len(acc_per_fold)):
  print('------------------------------------------------------------------------')
  print(f'> Fold {i+1} - Loss: {loss_per_fold[i]} - Accuracy: {acc_per_fold[i]}%')
print('------------------------------------------------------------------------')
print('Average scores for all folds:')
print(f'> Accuracy: {np.mean(acc_per_fold)} (+- {np.std(acc_per_fold)})')
print(f'> Loss: {np.mean(loss_per_fold)}')
print('------------------------------------------------------------------------')


# Add attention layer to the deep learning network
class attention(Layer):
    def __init__(self,**kwargs):
        super(attention,self).__init__(**kwargs)
 
    def build(self,input_shape):
        self.W=self.add_weight(name='attention_weight', shape=(input_shape[-1],1), 
                               initializer='random_normal', trainable=True)
        self.b=self.add_weight(name='attention_bias', shape=(input_shape[1],1), 
                               initializer='zeros', trainable=True)        
        super(attention, self).build(input_shape)
 
    def call(self,x):
        # Alignment scores. Pass them through tanh function
        e = K.tanh(K.dot(x,self.W)+self.b)
        # Remove dimension of size 1
        e = K.squeeze(e, axis=-1)   
        # Compute the weights
        alpha = K.softmax(e)
        # Reshape to tensorFlow format
        alpha = K.expand_dims(alpha, axis=-1)
        # Compute the context vector
        context = x * alpha
        context = K.sum(context, axis=1)
        return context
    
def create_CNNLSTM_with_attention(hidden_units, dense_units, input_shape, activation):
    model = Sequential()
    model.add(TimeDistributed(Conv1D(filters=64, kernel_size=3, activation='relu'), input_shape=(None,32,6)))
    model.add(TimeDistributed(Conv1D(filters=64, kernel_size=3, activation='relu')))
    model.add(TimeDistributed(Dropout(0.5)))
    model.add(TimeDistributed(MaxPooling1D(pool_size=2)))
    auto_feature=model.add(TimeDistributed(Flatten()))
    model.add(LSTM(100))
    model.add(Dropout(0.5))
    model.add(Dense(100, activation='relu'))
    model.add(Dense(n_outputs, activation='softmax'))
    concatenate_layer=model.add(Concatenate()([feature_input, auto_feature]))
    #dense=model.add(Dense(100)(concatenate_layer))
    attention_layer = attention()(concatenate_layer)
    #model.add(Dense(100)(attention_layer))
    outputs=Dense(100, trainable=True, activation=activation)(attention_layer)
    model.add(Dense(n_outputs, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])   
    return model    
    
for train, test in loso.split(reshaped_segments, labels):
	history_CNN = model.fit(reshaped_segments[train],
                    labels[train],
                    epochs=30,
                    batch_size=64,
                    verbose=1)
    # Generate generalization metrics
scores = model.evaluate(reshaped_segments[test], labels[test], verbose=0)
print('Score'': {model.metrics_names[0]} of {scores[0]}; {model.metrics_names[1]} of {scores[1]*100}%')
acc_per_fold.append(scores[1] * 100)
loss_per_fold.append(scores[0])
	
# Create the model with attention, train and evaluate
model_attention = create_CNNLSTM_with_attention(hidden_units=2, dense_units=1, 
                                  input_shape=(20,1), activation='tanh')
model_attention.summary()    
 
 
model_attention.fit(reshaped_segments[test], labels[test], epochs=30, batch_size=1, verbose=2)
 
# Evalute model
train_attn = model_attention.evaluate(reshaped_segments[test], labels[test])
test_attn = model_attention.evaluate(reshaped_segments[test], labels[test])

e = shap.DeepExplainer(model, reshaped_segments[train])
shap_values = e.shap_values(reshaped_segments[test])

# visualize the first prediction's explanation
shap.plots.waterfall(shap_values[0])# visualize the first prediction's explanation with a force plot
shap.plots.force(shap_values[0])

import matplotlib.pyplot as plt

#plt.savefig('/home/path/path/shap_summary.png', dpi=600)
#plt.savefig('C:/Users/Dipanwita/OneDrive/Desktop/shap_summery.eps', dpi=300, bbox_inches='tight')
plt.show()
fig=plt.gcf()
shap.summary_plot(shap_values, reshaped_segments)


